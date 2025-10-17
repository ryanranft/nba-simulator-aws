#!/usr/bin/env python3
"""
Export ML-Ready Quality Dataset

Exports comprehensive quality metadata for all games to enable quality-aware
machine learning training. Includes quality scores, uncertainty levels,
recommended sources, and training weights.

Output Format:
- JSON with metadata and per-game quality information
- CSV with training-ready features
- Summary statistics

Usage:
    python scripts/validation/export_ml_quality_dataset.py
    python scripts/validation/export_ml_quality_dataset.py --output-dir /custom/path
    python scripts/validation/export_ml_quality_dataset.py --format json
    python scripts/validation/export_ml_quality_dataset.py --format csv
    python scripts/validation/export_ml_quality_dataset.py --format both

Version: 1.0
Created: October 9, 2025
"""

import sqlite3
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import argparse
from collections import defaultdict

# Database path
UNIFIED_DB = "/tmp/unified_nba.db"

# Default output directory
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "ml_quality"


def get_quality_metadata(unified_conn) -> Dict:
    """Get overall quality metadata for the dataset."""

    cursor = unified_conn.cursor()

    # Total games
    cursor.execute("SELECT COUNT(*) FROM quality_scores;")
    total_games = cursor.fetchone()[0]

    # Quality distribution
    cursor.execute(
        """
        SELECT
            CASE
                WHEN quality_score >= 90 THEN 'high'
                WHEN quality_score >= 70 THEN 'medium'
                WHEN quality_score >= 50 THEN 'low'
                ELSE 'very_low'
            END as quality_level,
            COUNT(*) as count,
            ROUND(AVG(quality_score), 1) as avg_score,
            MIN(quality_score) as min_score,
            MAX(quality_score) as max_score
        FROM quality_scores
        GROUP BY quality_level
        ORDER BY avg_score DESC;
    """
    )

    quality_distribution = {}
    for row in cursor.fetchall():
        level, count, avg, min_score, max_score = row
        quality_distribution[level] = {
            "count": count,
            "percentage": round(count / total_games * 100, 2),
            "avg_score": avg,
            "min_score": min_score,
            "max_score": max_score,
        }

    # Uncertainty distribution
    cursor.execute(
        """
        SELECT uncertainty, COUNT(*)
        FROM quality_scores
        GROUP BY uncertainty
        ORDER BY uncertainty;
    """
    )

    uncertainty_distribution = {}
    for row in cursor.fetchall():
        uncertainty, count = row
        uncertainty_distribution[uncertainty] = {
            "count": count,
            "percentage": round(count / total_games * 100, 2),
        }

    # Source recommendations
    cursor.execute(
        """
        SELECT recommended_source, COUNT(*)
        FROM quality_scores
        WHERE recommended_source IS NOT NULL
        GROUP BY recommended_source
        ORDER BY COUNT(*) DESC;
    """
    )

    source_recommendations = {}
    for row in cursor.fetchall():
        source, count = row
        source_recommendations[source] = {
            "count": count,
            "percentage": round(count / total_games * 100, 2),
        }

    # Issue flags
    cursor.execute(
        """
        SELECT
            SUM(CASE WHEN has_event_count_issue THEN 1 ELSE 0 END) as event_count_issues,
            SUM(CASE WHEN has_coordinate_issue THEN 1 ELSE 0 END) as coordinate_issues,
            SUM(CASE WHEN has_score_issue THEN 1 ELSE 0 END) as score_issues,
            SUM(CASE WHEN has_timing_issue THEN 1 ELSE 0 END) as timing_issues,
            SUM(CASE WHEN use_for_training THEN 1 ELSE 0 END) as usable_for_training
        FROM quality_scores;
    """
    )

    row = cursor.fetchone()
    issue_summary = {
        "event_count_issues": row[0],
        "coordinate_issues": row[1],
        "score_issues": row[2],
        "timing_issues": row[3],
        "usable_for_training": row[4],
        "usable_percentage": round(row[4] / total_games * 100, 2),
    }

    # Source coverage
    cursor.execute(
        """
        SELECT
            SUM(CASE WHEN has_espn THEN 1 ELSE 0 END) as espn_games,
            SUM(CASE WHEN has_hoopr THEN 1 ELSE 0 END) as hoopr_games,
            SUM(CASE WHEN has_espn AND has_hoopr THEN 1 ELSE 0 END) as dual_source_games,
            SUM(CASE WHEN has_discrepancies THEN 1 ELSE 0 END) as games_with_discrepancies
        FROM source_coverage;
    """
    )

    row = cursor.fetchone()
    source_coverage = {
        "espn_games": row[0],
        "hoopr_games": row[1],
        "dual_source_games": row[2],
        "dual_source_percentage": round(row[2] / total_games * 100, 2),
        "games_with_discrepancies": row[3],
        "discrepancy_percentage": round(row[3] / total_games * 100, 2),
    }

    # Date range
    cursor.execute("SELECT MIN(game_date), MAX(game_date) FROM quality_scores;")
    min_date, max_date = cursor.fetchone()

    cursor.close()

    return {
        "dataset_metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_games": total_games,
            "date_range": {"start": min_date, "end": max_date},
            "data_sources": ["ESPN", "hoopR"],
        },
        "quality_distribution": quality_distribution,
        "uncertainty_distribution": uncertainty_distribution,
        "source_recommendations": source_recommendations,
        "issue_summary": issue_summary,
        "source_coverage": source_coverage,
    }


def get_all_games_quality(unified_conn) -> List[Dict]:
    """Get quality information for all games."""

    cursor = unified_conn.cursor()

    cursor.execute(
        """
        SELECT
            qs.game_id,
            qs.game_date,
            qs.recommended_source,
            qs.quality_score,
            qs.uncertainty,
            qs.has_event_count_issue,
            qs.has_coordinate_issue,
            qs.has_score_issue,
            qs.has_timing_issue,
            qs.use_for_training,
            qs.ml_notes,
            sc.has_espn,
            sc.has_hoopr,
            sc.espn_event_count,
            sc.hoopr_event_count,
            sc.has_discrepancies,
            sc.primary_source
        FROM quality_scores qs
        LEFT JOIN source_coverage sc ON qs.game_id = sc.game_id
        ORDER BY qs.game_date DESC, qs.game_id;
    """
    )

    games = []
    for row in cursor.fetchall():
        (
            game_id,
            game_date,
            recommended_source,
            quality_score,
            uncertainty,
            has_event_count_issue,
            has_coordinate_issue,
            has_score_issue,
            has_timing_issue,
            use_for_training,
            ml_notes,
            has_espn,
            has_hoopr,
            espn_event_count,
            hoopr_event_count,
            has_discrepancies,
            primary_source,
        ) = row

        # Calculate training weight (0.0 to 1.0 based on quality score)
        training_weight = quality_score / 100.0 if quality_score else 0.0

        # Determine quality level
        if quality_score >= 90:
            quality_level = "high"
        elif quality_score >= 70:
            quality_level = "medium"
        elif quality_score >= 50:
            quality_level = "low"
        else:
            quality_level = "very_low"

        games.append(
            {
                "game_id": game_id,
                "game_date": game_date,
                "recommended_source": recommended_source,
                "quality_score": quality_score,
                "quality_level": quality_level,
                "uncertainty": uncertainty,
                "training_weight": training_weight,
                "use_for_training": bool(use_for_training),
                "issues": {
                    "event_count": bool(has_event_count_issue),
                    "coordinates": bool(has_coordinate_issue),
                    "score": bool(has_score_issue),
                    "timing": bool(has_timing_issue),
                },
                "source_availability": {
                    "espn": bool(has_espn),
                    "hoopr": bool(has_hoopr),
                    "espn_event_count": espn_event_count,
                    "hoopr_event_count": hoopr_event_count,
                },
                "has_discrepancies": bool(has_discrepancies),
                "ml_notes": ml_notes,
            }
        )

    cursor.close()
    return games


def export_json(output_dir: Path, metadata: Dict, games: List[Dict]):
    """Export quality dataset as JSON."""

    output_file = (
        output_dir / f"ml_quality_dataset_{datetime.now().strftime('%Y%m%d')}.json"
    )

    data = {"metadata": metadata, "games": {game["game_id"]: game for game in games}}

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✓ JSON exported: {output_file}")
    print(f"  File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    return output_file


def export_csv(output_dir: Path, games: List[Dict]):
    """Export quality dataset as CSV (training-ready format)."""

    output_file = (
        output_dir / f"ml_quality_dataset_{datetime.now().strftime('%Y%m%d')}.csv"
    )

    # Flatten the nested structure for CSV
    fieldnames = [
        "game_id",
        "game_date",
        "quality_score",
        "quality_level",
        "uncertainty",
        "training_weight",
        "recommended_source",
        "use_for_training",
        "has_espn",
        "has_hoopr",
        "espn_event_count",
        "hoopr_event_count",
        "has_discrepancies",
        "has_event_count_issue",
        "has_coordinate_issue",
        "has_score_issue",
        "has_timing_issue",
        "ml_notes",
    ]

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for game in games:
            writer.writerow(
                {
                    "game_id": game["game_id"],
                    "game_date": game["game_date"],
                    "quality_score": game["quality_score"],
                    "quality_level": game["quality_level"],
                    "uncertainty": game["uncertainty"],
                    "training_weight": game["training_weight"],
                    "recommended_source": game["recommended_source"],
                    "use_for_training": game["use_for_training"],
                    "has_espn": game["source_availability"]["espn"],
                    "has_hoopr": game["source_availability"]["hoopr"],
                    "espn_event_count": game["source_availability"]["espn_event_count"],
                    "hoopr_event_count": game["source_availability"][
                        "hoopr_event_count"
                    ],
                    "has_discrepancies": game["has_discrepancies"],
                    "has_event_count_issue": game["issues"]["event_count"],
                    "has_coordinate_issue": game["issues"]["coordinates"],
                    "has_score_issue": game["issues"]["score"],
                    "has_timing_issue": game["issues"]["timing"],
                    "ml_notes": game["ml_notes"],
                }
            )

    print(f"✓ CSV exported: {output_file}")
    print(f"  File size: {output_file.stat().st_size / 1024:.2f} KB")
    return output_file


def export_summary(output_dir: Path, metadata: Dict):
    """Export summary statistics as markdown."""

    output_file = (
        output_dir / f"ml_quality_summary_{datetime.now().strftime('%Y%m%d')}.md"
    )

    with open(output_file, "w") as f:
        f.write("# ML Quality Dataset Summary\n\n")
        f.write(f"**Generated:** {metadata['dataset_metadata']['generated_at']}\n\n")
        f.write("---\n\n")

        # Dataset info
        f.write("## Dataset Information\n\n")
        f.write(f"- **Total games:** {metadata['dataset_metadata']['total_games']:,}\n")
        f.write(
            f"- **Date range:** {metadata['dataset_metadata']['date_range']['start']} to {metadata['dataset_metadata']['date_range']['end']}\n"
        )
        f.write(
            f"- **Data sources:** {', '.join(metadata['dataset_metadata']['data_sources'])}\n\n"
        )

        # Quality distribution
        f.write("## Quality Distribution\n\n")
        f.write("| Quality Level | Games | Percentage | Avg Score | Range |\n")
        f.write("|---------------|--------|------------|-----------|-------|\n")
        for level, stats in sorted(
            metadata["quality_distribution"].items(),
            key=lambda x: x[1]["avg_score"],
            reverse=True,
        ):
            f.write(
                f"| {level.title():13s} | {stats['count']:,} | {stats['percentage']:.1f}% | {stats['avg_score']} | {stats['min_score']}-{stats['max_score']} |\n"
            )
        f.write("\n")

        # Uncertainty distribution
        f.write("## Uncertainty Distribution\n\n")
        f.write("| Uncertainty | Games | Percentage |\n")
        f.write("|-------------|--------|------------|\n")
        for uncertainty, stats in metadata["uncertainty_distribution"].items():
            f.write(
                f"| {uncertainty:11s} | {stats['count']:,} | {stats['percentage']:.1f}% |\n"
            )
        f.write("\n")

        # Source recommendations
        f.write("## Recommended Sources\n\n")
        f.write("| Source | Games | Percentage |\n")
        f.write("|--------|--------|------------|\n")
        for source, stats in sorted(
            metadata["source_recommendations"].items(),
            key=lambda x: x[1]["count"],
            reverse=True,
        ):
            f.write(
                f"| {source:6s} | {stats['count']:,} | {stats['percentage']:.1f}% |\n"
            )
        f.write("\n")

        # Issue summary
        f.write("## Data Quality Issues\n\n")
        issues = metadata["issue_summary"]
        f.write(f"- **Event count issues:** {issues['event_count_issues']:,}\n")
        f.write(f"- **Coordinate issues:** {issues['coordinate_issues']:,}\n")
        f.write(f"- **Score issues:** {issues['score_issues']:,}\n")
        f.write(f"- **Timing issues:** {issues['timing_issues']:,}\n")
        f.write(
            f"- **Usable for training:** {issues['usable_for_training']:,} ({issues['usable_percentage']:.1f}%)\n\n"
        )

        # Source coverage
        f.write("## Source Coverage\n\n")
        coverage = metadata["source_coverage"]
        f.write(f"- **ESPN games:** {coverage['espn_games']:,}\n")
        f.write(f"- **hoopR games:** {coverage['hoopr_games']:,}\n")
        f.write(
            f"- **Dual-source games:** {coverage['dual_source_games']:,} ({coverage['dual_source_percentage']:.1f}%)\n"
        )
        f.write(
            f"- **Games with discrepancies:** {coverage['games_with_discrepancies']:,} ({coverage['discrepancy_percentage']:.1f}%)\n\n"
        )

        # ML guidance
        f.write("## ML Training Guidance\n\n")
        f.write("### Quality-Aware Training\n\n")
        f.write("```python\n")
        f.write("import pandas as pd\n\n")
        f.write("# Load quality dataset\n")
        f.write("df = pd.read_csv('ml_quality_dataset_YYYYMMDD.csv')\n\n")
        f.write("# Filter by quality level\n")
        f.write(
            "high_quality = df[df['quality_level'] == 'high']  # Best for validation\n"
        )
        f.write(
            "medium_quality = df[df['quality_level'] == 'medium']  # Use with weights\n"
        )
        f.write(
            "low_quality = df[df['quality_level'] == 'low']  # Use with caution\n\n"
        )
        f.write("# Use training weights\n")
        f.write(
            "sample_weight = df['training_weight']  # 0.0 to 1.0 based on quality\n\n"
        )
        f.write("# Filter by issues\n")
        f.write(
            "no_score_issues = df[~df['has_score_issue']]  # Games without score problems\n"
        )
        f.write("```\n\n")

        f.write("### Uncertainty Estimation\n\n")
        f.write("```python\n")
        f.write("# Output confidence intervals based on quality\n")
        f.write("def predict_with_uncertainty(model, X, quality_scores):\n")
        f.write("    predictions = model.predict(X)\n")
        f.write("    \n")
        f.write("    # Scale confidence by quality score\n")
        f.write("    confidence = quality_scores / 100.0\n")
        f.write("    \n")
        f.write("    # Wider intervals for lower quality\n")
        f.write("    interval_width = (1.0 - confidence) * predictions * 0.2\n")
        f.write("    \n")
        f.write("    return predictions, interval_width\n")
        f.write("```\n\n")

    print(f"✓ Summary exported: {output_file}")
    return output_file


def main():
    """Main execution."""

    parser = argparse.ArgumentParser(
        description="Export ML-ready quality dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export both JSON and CSV
  python scripts/validation/export_ml_quality_dataset.py

  # Export JSON only
  python scripts/validation/export_ml_quality_dataset.py --format json

  # Export to custom directory
  python scripts/validation/export_ml_quality_dataset.py --output-dir /custom/path

Output Files:
  - ml_quality_dataset_YYYYMMDD.json  - Complete quality metadata
  - ml_quality_dataset_YYYYMMDD.csv   - Training-ready CSV format
  - ml_quality_summary_YYYYMMDD.md    - Human-readable summary

Usage in ML:
  import pandas as pd
  df = pd.read_csv('ml_quality_dataset_YYYYMMDD.csv')

  # Quality-aware training
  sample_weight = df['training_weight']

  # Filter by quality
  high_quality = df[df['quality_level'] == 'high']
        """,
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )

    parser.add_argument(
        "--format",
        choices=["json", "csv", "both"],
        default="both",
        help="Export format (default: both)",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Connect to database
    print("Connecting to unified database...")
    unified_conn = sqlite3.connect(UNIFIED_DB)
    print(f"✓ Connected: {UNIFIED_DB}")
    print()

    # Get metadata
    print("=" * 70)
    print("COLLECTING QUALITY METADATA")
    print("=" * 70)
    print()
    metadata = get_quality_metadata(unified_conn)
    print(
        f"✓ Metadata collected: {metadata['dataset_metadata']['total_games']:,} games"
    )
    print()

    # Get all games
    print("=" * 70)
    print("LOADING GAME QUALITY DATA")
    print("=" * 70)
    print()
    games = get_all_games_quality(unified_conn)
    print(f"✓ Loaded {len(games):,} games with quality information")
    print()

    # Close database
    unified_conn.close()

    # Export files
    print("=" * 70)
    print("EXPORTING DATASETS")
    print("=" * 70)
    print()

    exported_files = []

    if args.format in ["json", "both"]:
        json_file = export_json(output_dir, metadata, games)
        exported_files.append(json_file)
        print()

    if args.format in ["csv", "both"]:
        csv_file = export_csv(output_dir, games)
        exported_files.append(csv_file)
        print()

    # Always export summary
    summary_file = export_summary(output_dir, metadata)
    exported_files.append(summary_file)
    print()

    # Final summary
    print("=" * 70)
    print("EXPORT COMPLETE")
    print("=" * 70)
    print()
    print(f"Exported {len(exported_files)} files to: {output_dir}")
    for file in exported_files:
        print(f"  - {file.name}")
    print()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
