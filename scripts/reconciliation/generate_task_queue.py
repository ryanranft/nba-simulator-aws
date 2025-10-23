#!/usr/bin/env python3
"""
Task Queue Generator - ADCE Phase 2A MVP
Generates prioritized collection tasks from detected gaps

Purpose:
- Read detected gaps (output of detect_data_gaps.py)
- Convert gaps into executable scraper tasks
- Map to appropriate scrapers
- Generate inventory/gaps.json for orchestrator

Output Format (inventory/gaps.json):
{
  "generated_at": "2025-10-22T19:30:00Z",
  "total_tasks": 450,
  "by_priority": {"critical": 25, "high": 120, ...},
  "tasks": [
    {
      "id": "task_001",
      "priority": "CRITICAL",
      "source": "espn",
      "data_type": "play_by_play",
      "season": "2024-25",
      "game_ids": [401579404, 401579405],
      "scraper": "espn_async_scraper",
      "estimated_time_minutes": 5,
      "reason": "Recent games missing"
    }
  ]
}

Usage:
    python generate_task_queue.py
    python generate_task_queue.py --gaps inventory/cache/detected_gaps.json
"""

import json
import yaml
import argparse
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TaskQueueGenerator:
    """
    Generates task queue from detected gaps

    Converts gap analysis into actionable scraper tasks
    """

    # Mapping of sources and data types to scrapers
    SCRAPER_MAPPING = {
        ("espn", "play_by_play"): "espn_async_scraper",
        ("espn", "box_scores"): "espn_async_scraper",
        ("espn", "schedule"): "espn_async_scraper",
        ("basketball_reference", "box_scores"): "basketball_reference_async_scraper",
        (
            "basketball_reference",
            "advanced_stats",
        ): "basketball_reference_async_scraper",
        ("nba_api", "player_tracking"): "nba_api_scraper",
        ("nba_api", "team_dashboards"): "nba_api_scraper",
        ("hoopr", "parquet_files"): "hoopr_incremental_scraper",
    }

    # Time estimates per task type (minutes)
    TIME_ESTIMATES = {
        "play_by_play": 2,
        "box_scores": 1,
        "schedule": 0.5,
        "advanced_stats": 3,
        "player_tracking": 5,
        "team_dashboards": 2,
        "parquet_files": 10,
    }

    def __init__(self, gaps_file, scraper_config_file="config/scraper_config.yaml"):
        """
        Initialize task queue generator

        Args:
            gaps_file: Path to detected gaps JSON
            scraper_config_file: Path to scraper config for validation
        """
        self.gaps_file = Path(gaps_file)
        self.scraper_config_file = Path(scraper_config_file)

        logger.info(f"Loading detected gaps from: {gaps_file}")
        with open(self.gaps_file, "r") as f:
            self.gaps = json.load(f)

        # Load scraper config for validation
        if self.scraper_config_file.exists():
            logger.info(f"Loading scraper config from: {scraper_config_file}")
            with open(self.scraper_config_file, "r") as f:
                self.scraper_config = yaml.safe_load(f)
        else:
            logger.warning("Scraper config not found, skipping validation")
            self.scraper_config = None

        self.task_counter = 0

    def generate_tasks(self):
        """
        Generate task queue from gaps

        Returns:
            dict: Complete task queue
        """
        logger.info("Starting task queue generation...")
        start_time = datetime.now()

        task_queue = {
            "generated_at": start_time.isoformat(),
            "gaps_file": str(self.gaps_file),
            "total_tasks": 0,
            "by_priority": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "by_source": defaultdict(int),
            "by_scraper": defaultdict(int),
            "estimated_total_minutes": 0,
            "tasks": [],
        }

        # Process gaps by priority (critical first)
        for priority in ["critical", "high", "medium", "low"]:
            gaps_at_priority = self.gaps["gaps"].get(priority, [])
            logger.info(f"Processing {len(gaps_at_priority)} {priority} gaps")

            for gap in gaps_at_priority:
                tasks = self._gap_to_tasks(gap, priority)

                for task in tasks:
                    task_queue["tasks"].append(task)
                    task_queue["total_tasks"] += 1
                    task_queue["by_priority"][priority] += 1
                    task_queue["by_source"][task["source"]] += 1
                    task_queue["by_scraper"][task["scraper"]] += 1
                    task_queue["estimated_total_minutes"] += task[
                        "estimated_time_minutes"
                    ]

        # Convert defaultdict to regular dict
        task_queue["by_source"] = dict(task_queue["by_source"])
        task_queue["by_scraper"] = dict(task_queue["by_scraper"])

        duration = (datetime.now() - start_time).total_seconds()
        task_queue["generation_duration_seconds"] = duration

        logger.info(f"Task queue generation complete in {duration:.1f}s")
        logger.info(f"Total tasks: {task_queue['total_tasks']}")
        logger.info(
            f"Estimated time: {task_queue['estimated_total_minutes']:.0f} minutes ({task_queue['estimated_total_minutes']/60:.1f} hours)"
        )

        return task_queue

    def _gap_to_tasks(self, gap, priority):
        """
        Convert a gap into one or more tasks

        Args:
            gap: Gap dict
            priority: Priority level

        Returns:
            list: List of task dicts
        """
        tasks = []
        gap_type = gap["gap_type"]

        if gap_type == "season_incomplete":
            # Create task for entire season
            task = self._create_season_task(gap, priority)
            if task:
                tasks.append(task)

        elif gap_type == "datatype_quality":
            # Create task for data type quality issues
            task = self._create_quality_task(gap, priority)
            if task:
                tasks.append(task)

        elif gap_type == "overall_completeness":
            # Create general backfill task
            task = self._create_backfill_task(gap, priority)
            if task:
                tasks.append(task)

        return tasks

    def _create_season_task(self, gap, priority):
        """Create task for incomplete season"""
        source = gap["source"]
        season = gap["season"]

        # For now, create a task for the entire season
        # Phase 3 orchestrator will break it down further

        # Determine data type (default to play_by_play)
        data_type = "play_by_play"  # Most common

        # Map to scraper
        scraper = self._map_to_scraper(source, data_type)
        if not scraper:
            logger.warning(f"No scraper mapping for {source}/{data_type}")
            return None

        # Estimate time
        missing_files = gap.get("missing_files", 0)
        time_per_file = self.TIME_ESTIMATES.get(data_type, 2)
        estimated_time = missing_files * time_per_file

        self.task_counter += 1
        task = {
            "id": f"task_{self.task_counter:06d}",
            "priority": priority.upper(),
            "gap_type": gap["gap_type"],
            "source": source,
            "season": season,
            "data_type": data_type,
            "scraper": scraper,
            "missing_files": missing_files,
            "estimated_time_minutes": estimated_time,
            "reason": gap["reason"],
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }

        return task

    def _create_quality_task(self, gap, priority):
        """Create task for data quality issues"""
        source = gap["source"]
        data_type = gap["data_type"]

        # Map to scraper
        scraper = self._map_to_scraper(source, data_type)
        if not scraper:
            logger.warning(f"No scraper mapping for {source}/{data_type}")
            return None

        # Estimate time for quality fixes
        stale_files = gap.get("stale_files", 0)
        small_files = gap.get("small_files", 0)
        total_files = stale_files + small_files
        time_per_file = self.TIME_ESTIMATES.get(data_type, 2)
        estimated_time = total_files * time_per_file

        self.task_counter += 1
        task = {
            "id": f"task_{self.task_counter:06d}",
            "priority": priority.upper(),
            "gap_type": gap["gap_type"],
            "source": source,
            "data_type": data_type,
            "scraper": scraper,
            "stale_files": stale_files,
            "small_files": small_files,
            "estimated_time_minutes": estimated_time,
            "reason": gap["reason"],
            "issues": gap.get("issues", [])[:3],  # First 3 issues
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }

        return task

    def _create_backfill_task(self, gap, priority):
        """Create task for general backfill"""
        source = gap["source"]

        # Default to play_by_play for backfill
        data_type = "play_by_play"

        # Map to scraper
        scraper = self._map_to_scraper(source, data_type)
        if not scraper:
            logger.warning(f"No scraper mapping for {source}/{data_type}")
            return None

        # Estimate time
        missing_files = gap.get("missing_files", 0)
        time_per_file = self.TIME_ESTIMATES.get(data_type, 2)
        estimated_time = missing_files * time_per_file

        self.task_counter += 1
        task = {
            "id": f"task_{self.task_counter:06d}",
            "priority": priority.upper(),
            "gap_type": gap["gap_type"],
            "source": source,
            "data_type": data_type,
            "scraper": scraper,
            "missing_files": missing_files,
            "completeness_pct": gap.get("completeness_pct", 0),
            "estimated_time_minutes": estimated_time,
            "reason": gap["reason"],
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }

        return task

    def _map_to_scraper(self, source, data_type):
        """Map source + data_type to appropriate scraper"""
        key = (source, data_type)
        scraper_name = self.SCRAPER_MAPPING.get(key)

        # Validate scraper exists in config
        if scraper_name and self.scraper_config:
            if scraper_name not in self.scraper_config.get("scrapers", {}):
                logger.warning(f"Scraper {scraper_name} not in config")
                return None

        return scraper_name

    def save_task_queue(self, task_queue, output_file="inventory/gaps.json"):
        """
        Save task queue to file

        Args:
            task_queue: Task queue dict
            output_file: Path to output file

        Returns:
            Path: Path to saved file
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving task queue to {output_path}")

        with open(output_path, "w") as f:
            json.dump(task_queue, f, indent=2, default=str)

        logger.info("Task queue saved successfully")
        return output_path


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate task queue from detected gaps"
    )
    parser.add_argument(
        "--gaps",
        default="inventory/cache/detected_gaps.json",
        help="Path to detected gaps JSON",
    )
    parser.add_argument(
        "--scraper-config",
        default="config/scraper_config.yaml",
        help="Path to scraper config for validation",
    )
    parser.add_argument(
        "--output", default="inventory/gaps.json", help="Output file path"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Generate tasks but don't save"
    )

    args = parser.parse_args()

    # Check file exists
    if not Path(args.gaps).exists():
        print(f"❌ Detected gaps file not found: {args.gaps}")
        print("Run detect_data_gaps.py first")
        return 1

    # Initialize generator
    generator = TaskQueueGenerator(
        gaps_file=args.gaps, scraper_config_file=args.scraper_config
    )

    # Generate task queue
    task_queue = generator.generate_tasks()

    # Save results
    if not args.dry_run:
        output_path = generator.save_task_queue(task_queue, args.output)
        print(f"\n✅ Task queue saved: {output_path}")
    else:
        print("\n🔍 DRY RUN - Results not saved")

    # Print summary
    print(f"\n📊 Task Queue Summary:")
    print(f"  Total tasks: {task_queue['total_tasks']}")
    print(
        f"  Estimated time: {task_queue['estimated_total_minutes']:.0f} min ({task_queue['estimated_total_minutes']/60:.1f} hrs)"
    )
    print(f"\n📋 By Priority:")
    for priority, count in task_queue["by_priority"].items():
        print(f"  {priority.upper()}: {count}")
    print(f"\n🔧 By Scraper:")
    for scraper, count in task_queue["by_scraper"].items():
        print(f"  {scraper}: {count}")

    # Show critical tasks
    critical_tasks = [t for t in task_queue["tasks"] if t["priority"] == "CRITICAL"]
    if critical_tasks:
        print(f"\n🚨 Critical Tasks (Top 5):")
        for i, task in enumerate(critical_tasks[:5], 1):
            print(f"  {i}. [{task['id']}] {task['scraper']} - {task['reason']}")

    return 0


if __name__ == "__main__":
    exit(main())
