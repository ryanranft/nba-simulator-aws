#!/usr/bin/env python3
"""
ESPN PBP Data Extractor - Optimized Version

Efficiently extracts play-by-play data from existing ESPN JSON files.
Focuses on recent seasons (2022-2025) and handles data structure variations.

Usage:
    python scripts/etl/extract_espn_pbp_optimized.py --seasons 2022-2025 --output-dir data/extracted_pbp
    python scripts/etl/extract_espn_pbp_optimized.py --quick-test --max-files 100

Version: 2.0
Created: October 13, 2025
"""

import json
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/espn_pbp_extraction_optimized.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class PlayByPlayEvent:
    """Clean PBP event structure"""

    game_id: str
    event_id: str
    period: int
    clock: str
    text: str
    home_away: str
    away_score: int
    home_score: int
    game_date: str
    season: str
    team_abbrev: Optional[str] = None
    player_name: Optional[str] = None
    event_type: Optional[str] = None


@dataclass
class GameInfo:
    """Game metadata"""

    game_id: str
    game_date: str
    season: str
    home_team: str
    away_team: str
    home_abbrev: str
    away_abbrev: str
    final_score_home: int
    final_score_away: int
    total_plays: int


def extract_single_file(
    file_path: Path,
) -> Optional[Tuple[GameInfo, List[PlayByPlayEvent]]]:
    """Extract data from a single file - designed for multiprocessing"""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        # Navigate to game data
        try:
            gamepackage = data["page"]["content"]["gamepackage"]
        except (KeyError, TypeError):
            return None

        # Extract game info
        game_info = extract_game_info(data, file_path.stem)
        if not game_info:
            return None

        # Extract plays
        plays = extract_plays(gamepackage, game_info)

        return game_info, plays

    except Exception as e:
        return None


def extract_game_info(data: Dict, game_id: str) -> Optional[GameInfo]:
    """Extract game metadata"""
    try:
        # Navigate to game data
        gamepackage = data["page"]["content"]["gamepackage"]

        # Get game date
        gm_info = gamepackage.get("gmInfo", {})
        game_date_str = gm_info.get("dtTm", "")

        if not game_date_str:
            return None

        # Parse date
        try:
            game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
            season = f"{game_date.year}-{str(game_date.year + 1)[2:]}"
        except:
            return None

        # Get teams from PBP data
        pbp_data = gamepackage.get("pbp", {})
        teams_data = pbp_data.get("tms", {})
        home_team = teams_data.get("home", {})
        away_team = teams_data.get("away", {})

        if not home_team or not away_team:
            return None

        return GameInfo(
            game_id=game_id,
            game_date=game_date_str,
            season=season,
            home_team=home_team.get("displayName", "Unknown"),
            away_team=away_team.get("displayName", "Unknown"),
            home_abbrev=home_team.get("abbrev", "UNK"),
            away_abbrev=away_team.get("abbrev", "UNK"),
            final_score_home=int(home_team.get("score", 0)),
            final_score_away=int(away_team.get("score", 0)),
            total_plays=0,  # Will be updated
        )

    except Exception as e:
        return None


def extract_plays(gamepackage: Dict, game_info: GameInfo) -> List[PlayByPlayEvent]:
    """Extract play-by-play events"""
    plays = []

    try:
        pbp_data = gamepackage.get("pbp", {})
        play_grps = pbp_data.get("playGrps", [])

        if not play_grps:
            return plays

        # Process each period
        for period_idx, period_plays in enumerate(play_grps):
            if not isinstance(period_plays, list):
                continue

            period_num = period_idx + 1

            # Process each play in the period
            for play_idx, play in enumerate(period_plays):
                if not isinstance(play, dict):
                    continue

                try:
                    event = PlayByPlayEvent(
                        game_id=game_info.game_id,
                        event_id=play.get(
                            "id", f"{game_info.game_id}_{period_num}_{play_idx}"
                        ),
                        period=period_num,
                        clock=play.get("clock", {}).get("displayValue", ""),
                        text=play.get("text", ""),
                        home_away=play.get("homeAway", ""),
                        away_score=play.get("awayScore", 0),
                        home_score=play.get("homeScore", 0),
                        game_date=game_info.game_date,
                        season=game_info.season,
                    )

                    plays.append(event)

                except Exception as e:
                    continue

        # Update total plays count
        game_info.total_plays = len(plays)

    except Exception as e:
        pass

    return plays


class ESPNPBPExtractorOptimized:
    """Optimized ESPN PBP data extractor with multiprocessing"""

    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            "files_processed": 0,
            "files_successful": 0,
            "files_failed": 0,
            "total_plays": 0,
            "games_processed": 0,
            "seasons": defaultdict(int),
        }

        logger.info(f"Initialized Optimized ESPN PBP Extractor")
        logger.info(f"Input directory: {self.input_dir}")
        logger.info(f"Output directory: {self.output_dir}")

    def filter_files_by_seasons(
        self, files: List[Path], seasons: List[str]
    ) -> List[Path]:
        """Filter files by seasons using multiprocessing"""
        logger.info(f"Filtering {len(files)} files for seasons: {seasons}")

        # Use multiprocessing to check file dates
        with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
            future_to_file = {
                executor.submit(self.check_file_season, file_path, seasons): file_path
                for file_path in files
            }

            filtered_files = []
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    if future.result():
                        filtered_files.append(file_path)
                except Exception as e:
                    continue

        logger.info(f"Filtered to {len(filtered_files)} files for target seasons")
        return filtered_files

    def check_file_season(self, file_path: Path, target_seasons: List[str]) -> bool:
        """Check if file belongs to target seasons"""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            gamepackage = data["page"]["content"]["gamepackage"]
            gm_info = gamepackage.get("gmInfo", {})
            game_date_str = gm_info.get("dtTm", "")

            if not game_date_str:
                return False

            try:
                game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
                season = f"{game_date.year}-{str(game_date.year + 1)[2:]}"
                return season in target_seasons
            except:
                return False

        except:
            return False

    def process_files_parallel(
        self, files: List[Path], max_workers: int = None
    ) -> Dict:
        """Process files in parallel using multiprocessing"""
        if max_workers is None:
            max_workers = min(mp.cpu_count(), 8)  # Limit to 8 workers

        logger.info(f"Processing {len(files)} files with {max_workers} workers...")

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(extract_single_file, file_path): file_path
                for file_path in files
            }

            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                self.stats["files_processed"] += 1

                if self.stats["files_processed"] % 1000 == 0:
                    logger.info(
                        f"Processed {self.stats['files_processed']}/{len(files)} files..."
                    )

                try:
                    result = future.result()
                    if result:
                        game_info, plays = result
                        self.save_game_data(game_info, plays)

                        self.stats["files_successful"] += 1
                        self.stats["total_plays"] += len(plays)
                        self.stats["games_processed"] += 1
                        self.stats["seasons"][game_info.season] += 1
                    else:
                        self.stats["files_failed"] += 1

                except Exception as e:
                    self.stats["files_failed"] += 1

        logger.info("File processing completed!")
        self._log_statistics()
        return self.stats

    def save_game_data(self, game_info: GameInfo, plays: List[PlayByPlayEvent]):
        """Save extracted game data to files"""
        try:
            # Save game info
            game_file = self.output_dir / f"{game_info.game_id}_game.json"
            with open(game_file, "w") as f:
                json.dump(asdict(game_info), f, indent=2)

            # Save plays
            plays_file = self.output_dir / f"{game_info.game_id}_plays.json"
            plays_data = [asdict(play) for play in plays]
            with open(plays_file, "w") as f:
                json.dump(plays_data, f, indent=2)

        except Exception as e:
            pass

    def _log_statistics(self):
        """Log processing statistics"""
        logger.info("=" * 50)
        logger.info("EXTRACTION STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Files processed: {self.stats['files_processed']:,}")
        logger.info(f"Files successful: {self.stats['files_successful']:,}")
        logger.info(f"Files failed: {self.stats['files_failed']:,}")
        logger.info(
            f"Success rate: {self.stats['files_successful']/self.stats['files_processed']*100:.1f}%"
        )
        logger.info(f"Total plays extracted: {self.stats['total_plays']:,}")
        logger.info(f"Games processed: {self.stats['games_processed']:,}")
        if self.stats["games_processed"] > 0:
            logger.info(
                f"Average plays per game: {self.stats['total_plays']/self.stats['games_processed']:.1f}"
            )

        logger.info("\nSeason breakdown:")
        for season, count in sorted(self.stats["seasons"].items()):
            logger.info(f"  {season}: {count:,} games")


def main():
    parser = argparse.ArgumentParser(
        description="Extract ESPN PBP data (optimized version)"
    )
    parser.add_argument(
        "--input-dir",
        default="data/nba_pbp",
        help="Input directory with ESPN JSON files",
    )
    parser.add_argument(
        "--output-dir",
        default="data/extracted_pbp_optimized",
        help="Output directory for extracted data",
    )
    parser.add_argument(
        "--seasons", nargs="+", help="Seasons to extract (e.g., 2022-23 2023-24)"
    )
    parser.add_argument(
        "--max-files", type=int, help="Maximum number of files to process"
    )
    parser.add_argument(
        "--quick-test", action="store_true", help="Quick test with limited files"
    )
    parser.add_argument(
        "--max-workers", type=int, help="Maximum number of worker processes"
    )

    args = parser.parse_args()

    # Create extractor
    extractor = ESPNPBPExtractorOptimized(args.input_dir, args.output_dir)

    # Get all files
    files = list(extractor.input_dir.glob("*.json"))
    logger.info(f"Found {len(files)} total files")

    # Apply filters
    if args.seasons:
        files = extractor.filter_files_by_seasons(files, args.seasons)

    if args.max_files:
        files = files[: args.max_files]

    if args.quick_test:
        files = files[:100]
        logger.info(f"Quick test mode: processing {len(files)} files")

    # Process files
    stats = extractor.process_files_parallel(files, args.max_workers)


if __name__ == "__main__":
    main()





