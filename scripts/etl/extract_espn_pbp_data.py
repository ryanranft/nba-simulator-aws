#!/usr/bin/env python3
"""
ESPN PBP Data Extractor

Extracts clean play-by-play data from existing ESPN JSON files.
Processes the nested HTML structure to extract actual NBA game data.

Usage:
    python scripts/etl/extract_espn_pbp_data.py --input-dir data/nba_pbp --output-dir data/extracted_pbp
    python scripts/etl/extract_espn_pbp_data.py --analyze-gaps --date-range 2022-2025
    python scripts/etl/extract_espn_pbp_data.py --load-to-db --batch-size 1000

Version: 1.0
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
import sqlite3
import asyncio
import aiofiles
from collections import defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/espn_pbp_extraction.log"),
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


class ESPNPBPExtractor:
    """Extracts clean PBP data from ESPN JSON files"""

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

        logger.info(f"Initialized ESPN PBP Extractor")
        logger.info(f"Input directory: {self.input_dir}")
        logger.info(f"Output directory: {self.output_dir}")

    def extract_game_data(
        self, file_path: Path
    ) -> Optional[Tuple[GameInfo, List[PlayByPlayEvent]]]:
        """Extract game data from a single ESPN JSON file"""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            # Navigate to game data
            gamepackage = data["page"]["content"]["gamepackage"]

            # Extract game info
            game_info = self._extract_game_info(data, file_path.stem)
            if not game_info:
                return None

            # Extract plays
            plays = self._extract_plays(gamepackage, game_info)

            return game_info, plays

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return None

    def _extract_game_info(self, data: Dict, game_id: str) -> Optional[GameInfo]:
        """Extract game metadata"""
        try:
            # Navigate to game data
            gamepackage = data["page"]["content"]["gamepackage"]

            # Get game date
            gm_info = gamepackage.get("gmInfo", {})
            game_date_str = gm_info.get("dtTm", "")

            if not game_date_str:
                logger.warning(f"No game date found for {game_id}")
                return None

            # Parse date
            try:
                game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
                season = f"{game_date.year}-{str(game_date.year + 1)[2:]}"
            except:
                logger.warning(f"Could not parse date {game_date_str} for {game_id}")
                return None

            # Get teams from PBP data
            pbp_data = gamepackage.get("pbp", {})
            teams_data = pbp_data.get("tms", {})
            home_team = teams_data.get("home", {})
            away_team = teams_data.get("away", {})

            if not home_team or not away_team:
                logger.warning(f"No team data found for {game_id}")
                return None

            return GameInfo(
                game_id=game_id,
                game_date=game_date_str,
                season=season,
                home_team=home_team.get("displayName", "Unknown"),
                away_team=away_team.get("displayName", "Unknown"),
                home_abbrev=home_team.get("abbrev", "UNK"),
                away_abbrev=away_team.get("abbrev", "UNK"),
                final_score_home=home_team.get("score", 0),
                final_score_away=away_team.get("score", 0),
                total_plays=0,  # Will be updated
            )

        except Exception as e:
            logger.error(f"Error extracting game info for {game_id}: {e}")
            return None

    def _extract_plays(
        self, gamepackage: Dict, game_info: GameInfo
    ) -> List[PlayByPlayEvent]:
        """Extract play-by-play events"""
        plays = []

        try:
            pbp_data = gamepackage.get("pbp", {})
            play_grps = pbp_data.get("playGrps", [])

            if not play_grps:
                logger.warning(f"No play groups found for {game_info.game_id}")
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
                        logger.warning(
                            f"Error processing play {play_idx} in period {period_num} for {game_info.game_id}: {e}"
                        )
                        continue

            # Update total plays count
            game_info.total_plays = len(plays)

        except Exception as e:
            logger.error(f"Error extracting plays for {game_info.game_id}: {e}")

        return plays

    def process_files(
        self,
        max_files: Optional[int] = None,
        date_range: Optional[Tuple[str, str]] = None,
    ) -> Dict:
        """Process all files in the input directory"""
        logger.info("Starting file processing...")

        files = list(self.input_dir.glob("*.json"))
        if max_files:
            files = files[:max_files]

        logger.info(f"Processing {len(files)} files...")

        for i, file_path in enumerate(files):
            if i % 1000 == 0:
                logger.info(f"Processed {i}/{len(files)} files...")

            self.stats["files_processed"] += 1

            # Extract data
            result = self.extract_game_data(file_path)
            if result:
                game_info, plays = result

                # Filter by date range if specified
                if date_range:
                    try:
                        game_date = datetime.fromisoformat(
                            game_info.game_date.replace("Z", "+00:00")
                        )
                        start_date = datetime.fromisoformat(date_range[0])
                        end_date = datetime.fromisoformat(date_range[1])

                        if not (start_date <= game_date <= end_date):
                            continue
                    except:
                        continue

                # Save extracted data
                self._save_game_data(game_info, plays)

                # Update statistics
                self.stats["files_successful"] += 1
                self.stats["total_plays"] += len(plays)
                self.stats["games_processed"] += 1
                self.stats["seasons"][game_info.season] += 1

            else:
                self.stats["files_failed"] += 1

        logger.info("File processing completed!")
        self._log_statistics()
        return self.stats

    def _save_game_data(self, game_info: GameInfo, plays: List[PlayByPlayEvent]):
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
            logger.error(f"Error saving data for {game_info.game_id}: {e}")

    def analyze_gaps(self, date_range: Tuple[str, str]) -> Dict:
        """Analyze data gaps for a specific date range"""
        logger.info(
            f"Analyzing gaps for date range: {date_range[0]} to {date_range[1]}"
        )

        files = list(self.input_dir.glob("*.json"))
        season_stats = defaultdict(
            lambda: {"total_games": 0, "successful_games": 0, "total_plays": 0}
        )

        start_date = datetime.fromisoformat(date_range[0])
        end_date = datetime.fromisoformat(date_range[1])

        for file_path in files:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)

                gamepackage = data["page"]["content"]["gamepackage"]
                gm_info = gamepackage.get("gmInfo", {})
                game_date_str = gm_info.get("dtTm", "")

                if not game_date_str:
                    continue

                game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))

                # Make dates timezone-aware for comparison
                start_date_tz = start_date.replace(tzinfo=timezone.utc)
                end_date_tz = end_date.replace(tzinfo=timezone.utc)

                if not (start_date_tz <= game_date <= end_date_tz):
                    continue

                season = f"{game_date.year}-{str(game_date.year + 1)[2:]}"
                season_stats[season]["total_games"] += 1

                # Check if we can extract plays
                pbp_data = gamepackage.get("pbp", {})
                play_grps = pbp_data.get("playGrps", [])

                if play_grps:
                    season_stats[season]["successful_games"] += 1

                    # Count total plays
                    total_plays = sum(
                        len(period) for period in play_grps if isinstance(period, list)
                    )
                    season_stats[season]["total_plays"] += total_plays

            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")
                continue

        # Calculate coverage
        gap_analysis = {}
        for season, stats in season_stats.items():
            coverage = (
                stats["successful_games"] / stats["total_games"] * 100
                if stats["total_games"] > 0
                else 0
            )
            gap_analysis[season] = {
                "total_games": stats["total_games"],
                "successful_games": stats["successful_games"],
                "coverage_percent": coverage,
                "total_plays": stats["total_plays"],
                "avg_plays_per_game": (
                    stats["total_plays"] / stats["successful_games"]
                    if stats["successful_games"] > 0
                    else 0
                ),
            }

        logger.info("Gap analysis completed!")
        return gap_analysis

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
        else:
            logger.info("Average plays per game: N/A (no games processed)")

        logger.info("\nSeason breakdown:")
        for season, count in sorted(self.stats["seasons"].items()):
            logger.info(f"  {season}: {count:,} games")


def main():
    parser = argparse.ArgumentParser(
        description="Extract ESPN PBP data from existing JSON files"
    )
    parser.add_argument(
        "--input-dir",
        default="data/nba_pbp",
        help="Input directory with ESPN JSON files",
    )
    parser.add_argument(
        "--output-dir",
        default="data/extracted_pbp",
        help="Output directory for extracted data",
    )
    parser.add_argument(
        "--max-files", type=int, help="Maximum number of files to process"
    )
    parser.add_argument(
        "--analyze-gaps",
        action="store_true",
        help="Analyze data gaps instead of extracting",
    )
    parser.add_argument(
        "--date-range",
        nargs=2,
        metavar=("START", "END"),
        help="Date range for analysis (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--load-to-db", action="store_true", help="Load extracted data to database"
    )
    parser.add_argument(
        "--batch-size", type=int, default=1000, help="Batch size for database loading"
    )

    args = parser.parse_args()

    # Create extractor
    extractor = ESPNPBPExtractor(args.input_dir, args.output_dir)

    if args.analyze_gaps:
        if not args.date_range:
            logger.error("Date range required for gap analysis")
            return

        gap_analysis = extractor.analyze_gaps(tuple(args.date_range))

        print("\n" + "=" * 60)
        print("DATA GAP ANALYSIS")
        print("=" * 60)
        for season, stats in gap_analysis.items():
            print(f"\n{season}:")
            print(f"  Total games: {stats['total_games']:,}")
            print(f"  Successful games: {stats['successful_games']:,}")
            print(f"  Coverage: {stats['coverage_percent']:.1f}%")
            print(f"  Total plays: {stats['total_plays']:,}")
            print(f"  Avg plays per game: {stats['avg_plays_per_game']:.1f}")

    else:
        # Extract data
        stats = extractor.process_files(args.max_files, args.date_range)

        if args.load_to_db:
            logger.info("Loading data to database...")
            # TODO: Implement database loading
            logger.info("Database loading not yet implemented")


if __name__ == "__main__":
    main()
