#!/usr/bin/env python3
"""
Comprehensive data quality analysis across all NBA JSON file types.

Analyzes:
- Play-by-Play (pbp): Check for actual play data
- Box Scores: Check for player statistics
- Team Stats: Check for team statistics
- Schedule: Check for game information

Usage:
    python scripts/analysis/comprehensive_data_analysis.py
"""

import json
import random
from pathlib import Path
from typing import Dict, Tuple


def check_pbp_data(file_path: Path) -> Tuple[bool, Dict]:
    """Check if PBP file has play-by-play data."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        pkg = data.get("page", {}).get("content", {}).get("gamepackage", {})

        # Check play-by-play
        playGrps = pkg.get("pbp", {}).get("playGrps", [])
        play_count = sum(len(period) for period in playGrps if isinstance(period, list))

        # Check shot chart
        shot_count = len(pkg.get("shtChrt", {}).get("plays", []))

        return play_count > 0, {
            "plays": play_count,
            "shots": shot_count,
            "has_gmInfo": "gmInfo" in pkg,
            "size_kb": file_path.stat().st_size / 1024,
        }
    except Exception as e:
        return False, {"error": str(e)}


def check_box_score_data(file_path: Path) -> Tuple[bool, Dict]:
    """Check if box score file has player statistics."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        pkg = data.get("page", {}).get("content", {}).get("gamepackage", {})
        boxscore = pkg.get("boxscore", {})

        # Count players with statistics
        player_count = 0
        if "players" in boxscore:
            for team in boxscore["players"]:
                if isinstance(team, dict) and "statistics" in team:
                    for stat_group in team["statistics"]:
                        if "athletes" in stat_group:
                            player_count += len(stat_group["athletes"])

        return player_count > 0, {
            "players": player_count,
            "has_boxscore": "boxscore" in pkg,
            "size_kb": file_path.stat().st_size / 1024,
        }
    except Exception as e:
        return False, {"error": str(e)}


def check_team_stats_data(file_path: Path) -> Tuple[bool, Dict]:
    """Check if team stats file has team statistics."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        pkg = data.get("page", {}).get("content", {}).get("gamepackage", {})
        boxscore = pkg.get("boxscore", {})

        # Check for team statistics
        team_count = 0
        team_stats = []
        if "teams" in boxscore:
            teams = boxscore["teams"]
            team_count = len(teams)

            # Check if teams have statistics
            for team in teams:
                if isinstance(team, dict) and "statistics" in team:
                    team_stats.append(len(team["statistics"]))

        return team_count > 0, {
            "teams": team_count,
            "has_stats": sum(team_stats) > 0 if team_stats else False,
            "size_kb": file_path.stat().st_size / 1024,
        }
    except Exception as e:
        return False, {"error": str(e)}


def check_schedule_data(file_path: Path) -> Tuple[bool, Dict]:
    """Check if schedule file has game information."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        # Schedule files have different structure
        content = data.get("page", {}).get("content", {})

        # Check for schedule/scoreboard data
        game_count = 0
        if "sbData" in content:
            events = content["sbData"].get("events", [])
            game_count = len(events)

        return game_count > 0, {
            "games": game_count,
            "has_sbData": "sbData" in content,
            "size_kb": file_path.stat().st_size / 1024,
        }
    except Exception as e:
        return False, {"error": str(e)}


def analyze_directory(
    dir_path: Path, check_func, data_type: str, sample_size: int = 300
):
    """Analyze a directory of JSON files."""
    print(f"\n{'='*70}")
    print(f"Analyzing {data_type.upper()}")
    print(f"{'='*70}")

    if not dir_path.exists():
        print(f"❌ Directory not found: {dir_path}")
        return None

    all_files = list(dir_path.glob("*.json"))
    total_files = len(all_files)

    print(f"Total files: {total_files:,}")

    if total_files == 0:
        return None

    # Sample files
    sample_files = random.sample(all_files, min(sample_size, total_files))
    print(f"Sampling: {len(sample_files)} files")

    valid_files = []
    empty_files = []
    error_files = []

    # Analyze each file
    for i, file_path in enumerate(sample_files):
        if (i + 1) % 100 == 0:
            print(f"  Processed {i+1}/{len(sample_files)}...")

        has_data, info = check_func(file_path)

        if "error" in info:
            error_files.append((file_path.name, info))
        elif has_data:
            valid_files.append((file_path.name, info))
        else:
            empty_files.append((file_path.name, info))

    # Calculate statistics
    valid_pct = (len(valid_files) / len(sample_files)) * 100
    empty_pct = (len(empty_files) / len(sample_files)) * 100
    error_pct = (len(error_files) / len(sample_files)) * 100

    est_valid = int((len(valid_files) / len(sample_files)) * total_files)
    est_empty = total_files - est_valid

    # Print results
    print(f"\n📊 Results:")
    print(
        f"  ✅ Valid:  {len(valid_files):4d} / {len(sample_files)} ({valid_pct:5.1f}%)"
    )
    print(
        f"  ❌ Empty:  {len(empty_files):4d} / {len(sample_files)} ({empty_pct:5.1f}%)"
    )
    print(
        f"  ⚠️  Errors: {len(error_files):4d} / {len(sample_files)} ({error_pct:5.1f}%)"
    )

    print(f"\n📈 Estimated Full Dataset:")
    print(f"  ✅ Valid:  ~{est_valid:,} files ({valid_pct:.1f}%)")
    print(f"  ❌ Empty:  ~{est_empty:,} files ({empty_pct:.1f}%)")

    # Sample files
    if valid_files:
        print(f"\n✅ Sample Valid Files:")
        for fname, info in valid_files[:3]:
            info_str = ", ".join(f"{k}={v}" for k, v in info.items() if k != "error")
            print(f"  {fname}: {info_str}")

    if empty_files:
        print(f"\n❌ Sample Empty Files:")
        for fname, info in empty_files[:3]:
            print(f"  {fname}: size={info.get('size_kb', 0):.1f} KB")

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
    }


def main():
    """Main analysis function."""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE NBA DATA QUALITY ANALYSIS")
    print("=" * 70)

    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"

    results = {}

    # 1. Play-by-Play
    print("\n" + "=" * 70)
    print("1/4: PLAY-BY-PLAY DATA")
    print("=" * 70)
    pbp_dir = data_dir / "nba_pbp"
    results["pbp"] = analyze_directory(
        pbp_dir, check_pbp_data, "play-by-play", sample_size=300
    )

    # 2. Box Scores
    print("\n" + "=" * 70)
    print("2/4: BOX SCORE DATA")
    print("=" * 70)
    box_dir = data_dir / "nba_box_score"
    results["box"] = analyze_directory(
        box_dir, check_box_score_data, "box scores", sample_size=300
    )

    # 3. Team Stats
    print("\n" + "=" * 70)
    print("3/4: TEAM STATS DATA")
    print("=" * 70)
    team_dir = data_dir / "nba_team_stats"
    results["team"] = analyze_directory(
        team_dir, check_team_stats_data, "team stats", sample_size=300
    )

    # 4. Schedule
    print("\n" + "=" * 70)
    print("4/4: SCHEDULE DATA")
    print("=" * 70)
    schedule_dir = data_dir / "nba_schedule_json"
    results["schedule"] = analyze_directory(
        schedule_dir, check_schedule_data, "schedule", sample_size=300
    )

    # Overall Summary
    print("\n" + "=" * 70)
    print("OVERALL SUMMARY")
    print("=" * 70)

    total_files = sum(r["total_files"] for r in results.values() if r)
    total_valid = sum(r["est_valid"] for r in results.values() if r)
    total_empty = sum(r["est_empty"] for r in results.values() if r)

    print(f"\n📊 Across All Data Types:")
    print(f"  Total files:      {total_files:,}")
    print(f"  Est. valid:       {total_valid:,} ({(total_valid/total_files*100):.1f}%)")
    print(f"  Est. empty:       {total_empty:,} ({(total_empty/total_files*100):.1f}%)")

    print(f"\n📁 By Data Type:")
    for name, result in results.items():
        if result:
            print(
                f"  {name.upper():12s}: {result['est_valid']:6,} / {result['total_files']:6,} valid ({result['valid_pct']:5.1f}%)"
            )

    print(f"\n💾 Storage Impact:")
    # Estimate based on average file sizes
    avg_file_size_mb = 0.8  # ~800 KB average
    total_gb = (total_files * avg_file_size_mb) / 1024
    valid_gb = (total_valid * 0.9) / 1024  # Valid files slightly larger
    waste_gb = total_gb - valid_gb

    print(f"  Total S3 storage: ~{total_gb:.1f} GB")
    print(
        f"  Usable data:      ~{valid_gb:.1f} GB ({(total_valid/total_files*100):.1f}%)"
    )
    print(
        f"  Waste:            ~{waste_gb:.1f} GB ({(total_empty/total_files*100):.1f}%)"
    )

    print(f"\n⚡ ETL Impact:")
    compute_waste_pct = (total_empty / total_files) * 100
    cost_savings = (compute_waste_pct / 100) * 13  # Based on $13/month ETL estimate

    print(f"  Files to skip:    {total_empty:,} ({compute_waste_pct:.1f}%)")
    print(f"  Compute savings:  ~${cost_savings:.2f}/month by pre-filtering")
    print(f"  Runtime savings:  ~{compute_waste_pct:.0f}% faster ETL")

    print(f"\n🎯 Recommendations:")
    print(f"  1. Pre-filter ALL file types in Glue ETL before processing")
    print(
        f"  2. Expected to reduce processing from {total_files:,} → {total_valid:,} files"
    )
    print(f"  3. Document filter criteria for each data type")
    print(f"  4. Consider creating 'valid file manifest' for future runs")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
