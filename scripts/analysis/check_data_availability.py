#!/usr/bin/env python3
"""
Analyze data availability across NBA JSON files.

This script checks which files contain actual game data vs just ESPN metadata.
Critical for ETL planning - not all files have usable data.

Usage:
    python scripts/analysis/check_data_availability.py
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple


def check_pbp_file(file_path: Path) -> Dict[str, any]:
    """
    Check if a play-by-play file contains actual play data.

    Args:
        file_path: Path to the PBP JSON file

    Returns:
        Dict with: has_plays, play_count, file_size, error (if any)
    """
    try:
        file_size = file_path.stat().st_size

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Look for plays in shtChrt (shot chart) section
        plays = []
        if "gamepackageJSON" in data:
            if "shtChrt" in data["gamepackageJSON"]:
                plays = data["gamepackageJSON"]["shtChrt"].get("plays", [])

        return {
            "has_plays": len(plays) > 0,
            "play_count": len(plays),
            "file_size": file_size,
            "error": None,
        }
    except Exception as e:
        return {
            "has_plays": False,
            "play_count": 0,
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "error": str(e),
        }


def check_box_score_file(file_path: Path) -> Dict[str, any]:
    """
    Check if a box score file contains player statistics.

    Args:
        file_path: Path to the box score JSON file

    Returns:
        Dict with: has_stats, player_count, file_size, error (if any)
    """
    try:
        file_size = file_path.stat().st_size

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Look for player stats in boxscore section
        player_count = 0
        if "gamepackageJSON" in data:
            if "boxscore" in data["gamepackageJSON"]:
                boxscore = data["gamepackageJSON"]["boxscore"]
                if "players" in boxscore:
                    for team in boxscore["players"]:
                        if "statistics" in team:
                            for stat_group in team["statistics"]:
                                if "athletes" in stat_group:
                                    player_count += len(stat_group["athletes"])

        return {
            "has_stats": player_count > 0,
            "player_count": player_count,
            "file_size": file_size,
            "error": None,
        }
    except Exception as e:
        return {
            "has_stats": False,
            "player_count": 0,
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "error": str(e),
        }


def check_schedule_file(file_path: Path) -> Dict[str, any]:
    """
    Check if a schedule file contains game information.

    Args:
        file_path: Path to the schedule JSON file

    Returns:
        Dict with: has_games, game_count, file_size, error (if any)
    """
    try:
        file_size = file_path.stat().st_size

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Look for games in content.sbData section
        game_count = 0
        if "content" in data:
            if "sbData" in data["content"]:
                if "events" in data["content"]["sbData"]:
                    game_count = len(data["content"]["sbData"]["events"])

        return {
            "has_games": game_count > 0,
            "game_count": game_count,
            "file_size": file_size,
            "error": None,
        }
    except Exception as e:
        return {
            "has_games": False,
            "game_count": 0,
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "error": str(e),
        }


def check_team_stats_file(file_path: Path) -> Dict[str, any]:
    """
    Check if a team stats file contains team statistics.

    Args:
        file_path: Path to the team stats JSON file

    Returns:
        Dict with: has_stats, team_count, file_size, error (if any)
    """
    try:
        file_size = file_path.stat().st_size

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Look for team stats in boxscore section
        team_count = 0
        if "gamepackageJSON" in data:
            if "boxscore" in data["gamepackageJSON"]:
                if "teams" in data["gamepackageJSON"]["boxscore"]:
                    team_count = len(data["gamepackageJSON"]["boxscore"]["teams"])

        return {
            "has_stats": team_count > 0,
            "team_count": team_count,
            "file_size": file_size,
            "error": None,
        }
    except Exception as e:
        return {
            "has_stats": False,
            "team_count": 0,
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "error": str(e),
        }


def analyze_directory(
    dir_path: Path, check_func, file_type: str, sample_size: int = 100
) -> Dict:
    """
    Analyze a directory of JSON files to check data availability.

    Args:
        dir_path: Path to directory containing JSON files
        check_func: Function to check each file
        file_type: Type of files being checked (for display)
        sample_size: Number of files to sample

    Returns:
        Dict with analysis results
    """
    print(f"\n{'='*70}")
    print(f"Analyzing {file_type} files in: {dir_path.name}/")
    print(f"{'='*70}")

    if not dir_path.exists():
        print(f"❌ Directory not found: {dir_path}")
        return {}

    # Get all JSON files
    all_files = list(dir_path.glob("*.json"))
    total_files = len(all_files)

    print(f"Total files: {total_files:,}")

    if total_files == 0:
        return {}

    # Sample files for analysis
    import random

    sample_files = random.sample(all_files, min(sample_size, total_files))

    print(f"Sampling: {len(sample_files)} files")
    print()

    # Check each sampled file
    valid_files = []
    empty_files = []
    error_files = []

    for file_path in sample_files:
        result = check_func(file_path)

        if result["error"]:
            error_files.append((file_path.name, result))
        elif file_type == "play-by-play" and result["has_plays"]:
            valid_files.append((file_path.name, result))
        elif file_type == "box_scores" and result["has_stats"]:
            valid_files.append((file_path.name, result))
        elif file_type == "schedule" and result["has_games"]:
            valid_files.append((file_path.name, result))
        elif file_type == "team_stats" and result["has_stats"]:
            valid_files.append((file_path.name, result))
        else:
            empty_files.append((file_path.name, result))

    # Calculate statistics
    valid_pct = (len(valid_files) / len(sample_files)) * 100
    empty_pct = (len(empty_files) / len(sample_files)) * 100
    error_pct = (len(error_files) / len(sample_files)) * 100

    # Estimate for full dataset
    est_valid = int((len(valid_files) / len(sample_files)) * total_files)
    est_empty = int((len(empty_files) / len(sample_files)) * total_files)
    est_errors = int((len(error_files) / len(sample_files)) * total_files)

    # Print results
    print(f"📊 Sample Results:")
    print(
        f"  ✅ Valid:  {len(valid_files):3d} / {len(sample_files)} ({valid_pct:5.1f}%)"
    )
    print(
        f"  ❌ Empty:  {len(empty_files):3d} / {len(sample_files)} ({empty_pct:5.1f}%)"
    )
    print(
        f"  ⚠️  Errors: {len(error_files):3d} / {len(sample_files)} ({error_pct:5.1f}%)"
    )
    print()
    print(f"📈 Estimated Full Dataset:")
    print(f"  ✅ Valid:  ~{est_valid:,} files")
    print(f"  ❌ Empty:  ~{est_empty:,} files")
    print(f"  ⚠️  Errors: ~{est_errors:,} files")

    # Show file size ranges
    if valid_files:
        valid_sizes = [r["file_size"] for _, r in valid_files]
        avg_valid_size = sum(valid_sizes) / len(valid_sizes)
        print(f"\n📦 Valid File Sizes:")
        print(f"  Average: {avg_valid_size/1024:.1f} KB")
        print(
            f"  Range:   {min(valid_sizes)/1024:.1f} KB - {max(valid_sizes)/1024:.1f} KB"
        )

    if empty_files:
        empty_sizes = [r["file_size"] for _, r in empty_files]
        avg_empty_size = sum(empty_sizes) / len(empty_sizes)
        print(f"\n📦 Empty File Sizes:")
        print(f"  Average: {avg_empty_size/1024:.1f} KB")
        print(
            f"  Range:   {min(empty_sizes)/1024:.1f} KB - {max(empty_sizes)/1024:.1f} KB"
        )

    # Show sample valid and empty files
    print(f"\n🔍 Sample Valid Files:")
    for fname, result in valid_files[:3]:
        if file_type == "play-by-play":
            print(
                f"  {fname} - {result['play_count']} plays, {result['file_size']/1024:.1f} KB"
            )
        elif file_type == "box_scores":
            print(
                f"  {fname} - {result['player_count']} players, {result['file_size']/1024:.1f} KB"
            )
        elif file_type == "schedule":
            print(
                f"  {fname} - {result['game_count']} games, {result['file_size']/1024:.1f} KB"
            )
        elif file_type == "team_stats":
            print(
                f"  {fname} - {result['team_count']} teams, {result['file_size']/1024:.1f} KB"
            )

    if empty_files:
        print(f"\n🔍 Sample Empty Files:")
        for fname, result in empty_files[:3]:
            print(f"  {fname} - {result['file_size']/1024:.1f} KB")

    # Show errors if any
    if error_files:
        print(f"\n⚠️  Sample Errors:")
        for fname, result in error_files[:3]:
            print(f"  {fname} - {result['error']}")

    return {
        "total_files": total_files,
        "sample_size": len(sample_files),
        "valid_count": len(valid_files),
        "empty_count": len(empty_files),
        "error_count": len(error_files),
        "valid_pct": valid_pct,
        "empty_pct": empty_pct,
        "est_valid": est_valid,
        "est_empty": est_empty,
        "est_errors": est_errors,
    }


def main():
    """Main analysis function."""
    print("\n" + "=" * 70)
    print("NBA Data Availability Analysis")
    print("=" * 70)
    print("\nChecking which files contain actual game data vs ESPN metadata...\n")

    # Project root
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"

    # Analyze each data type
    results = {}

    # Play-by-play
    pbp_dir = data_dir / "nba_pbp"
    results["pbp"] = analyze_directory(
        pbp_dir, check_pbp_file, "play-by-play", sample_size=200
    )

    # Box scores
    box_dir = data_dir / "nba_box_score"
    results["box"] = analyze_directory(
        box_dir, check_box_score_file, "box_scores", sample_size=200
    )

    # Schedule
    schedule_dir = data_dir / "nba_schedule_json"
    results["schedule"] = analyze_directory(
        schedule_dir, check_schedule_file, "schedule", sample_size=200
    )

    # Team stats
    team_dir = data_dir / "nba_team_stats"
    results["team"] = analyze_directory(
        team_dir, check_team_stats_file, "team_stats", sample_size=200
    )

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY: Data Availability Across All File Types")
    print(f"{'='*70}")

    total_valid = sum(r.get("est_valid", 0) for r in results.values())
    total_files = sum(r.get("total_files", 0) for r in results.values())

    print(f"\n📊 Overall Statistics:")
    print(f"  Total files:        {total_files:,}")
    print(
        f"  Est. valid files:   {total_valid:,} ({(total_valid/total_files*100):.1f}%)"
    )
    print(
        f"  Est. empty files:   {total_files - total_valid:,} ({((total_files-total_valid)/total_files*100):.1f}%)"
    )

    print(f"\n💾 Storage Impact:")
    print(f"  Current S3:         119 GB (all files)")
    print(f"  Est. valid data:    ~{(total_valid/total_files*119):.1f} GB")
    print(
        f"  Est. waste:         ~{((total_files-total_valid)/total_files*119):.1f} GB"
    )

    print(f"\n⚠️  ETL IMPLICATIONS:")
    print(f"  - Not all files contain usable game data")
    print(f"  - Filter files BEFORE processing to save compute time")
    print(f"  - Consider file size thresholds for quick filtering")
    print(f"  - Document which game IDs/patterns have valid data")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
