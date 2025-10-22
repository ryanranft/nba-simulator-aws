#!/usr/bin/env python3
"""
ESPN Shot Chart Extractor

Extracts shot chart data with coordinates from ESPN PBP JSON files.
Links to temporal box score snapshots for spatial + temporal analytics.

Data source: ESPN shot chart data (gamepackage.shtChrt)
Coverage: 31,241 games with PBP (1993-2025)
Coordinates: x, y (0-50 court width, 0-47 court length)

Created: October 18, 2025
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ESPNShotEvent:
    """Shot event extracted from ESPN shot chart data"""
    # Identifiers
    espn_play_id: str
    game_id: str
    player_id: str
    player_name: str

    # Shot details
    shot_made: bool
    shot_type_id: str
    shot_type_text: str
    shot_description: str

    # Spatial
    coordinate_x: int
    coordinate_y: int

    # Temporal
    period: int

    # Context
    home_away: str  # 'home' or 'away'


class ESPNShotChartExtractor:
    """Extract shot chart data from ESPN PBP JSON files"""

    def __init__(self, data_dir: str = "data/nba_pbp",
                 db_path: str = "/tmp/basketball_reference_boxscores.db"):
        """
        Initialize extractor.

        Args:
            data_dir: Directory containing ESPN PBP JSON files
            db_path: SQLite database path for shot_event_snapshots
        """
        self.data_dir = Path(data_dir)
        self.db_path = db_path
        self.conn = None

    def connect_db(self):
        """Connect to SQLite database"""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def extract_shot_chart_from_file(self, file_path: Path) -> Tuple[str, List[ESPNShotEvent]]:
        """
        Extract shot chart data from a single ESPN JSON file.

        Args:
            file_path: Path to ESPN PBP JSON file

        Returns:
            Tuple of (game_id, list of shot events)
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading {file_path}: {e}")
            return (None, [])

        # Extract game ID from filename
        game_id = file_path.stem

        # Navigate to shot chart data
        shot_chart = (
            data.get('page', {})
            .get('content', {})
            .get('gamepackage', {})
            .get('shtChrt', {})
        )

        if not shot_chart:
            logger.debug(f"No shot chart data for game {game_id}")
            return (game_id, [])

        # Extract plays
        plays = shot_chart.get('plays', [])

        shot_events = []
        for play in plays:
            # Only process shooting plays
            if not play.get('shootingPlay'):
                continue

            # Extract shot event
            shot_event = ESPNShotEvent(
                espn_play_id=play.get('id', ''),
                game_id=game_id,
                player_id=play.get('athlete', {}).get('id', ''),
                player_name=play.get('athlete', {}).get('name', ''),
                shot_made=play.get('scoringPlay', False),
                shot_type_id=play.get('type', {}).get('id', ''),
                shot_type_text=play.get('type', {}).get('txt', ''),
                shot_description=play.get('text', ''),
                coordinate_x=play.get('coordinate', {}).get('x', 0),
                coordinate_y=play.get('coordinate', {}).get('y', 0),
                period=play.get('period', {}).get('number', 0),
                home_away=play.get('homeAway', '')
            )

            shot_events.append(shot_event)

        return (game_id, shot_events)

    def classify_shot_zone(self, x: int, y: int, shot_type: str) -> str:
        """
        Classify shot into zone based on coordinates.

        ESPN coordinates: 0-50 (width) × 0-47 (length)
        Basket location: ~25, ~5

        Args:
            x: X coordinate (0-50)
            y: Y coordinate (0-47)
            shot_type: Shot type text

        Returns:
            Zone classification
        """
        # Basket location (approximate)
        basket_x, basket_y = 25, 5

        # Calculate distance from basket
        distance = ((x - basket_x)**2 + (y - basket_y)**2)**0.5

        # Check if three-point shot based on description
        is_three = 'three' in shot_type.lower() or 'three point' in shot_type.lower()

        if is_three:
            # Corner three: near sidelines
            if x < 10 or x > 40:
                return 'corner_three'
            else:
                return 'above_break_three'
        else:
            # Two-point zones
            if distance <= 5:
                return 'paint'
            elif distance <= 10:
                return 'short_mid'
            elif distance <= 16:
                return 'long_mid'
            else:
                return 'deep_two'

    def determine_shot_type(self, shot_type_text: str) -> str:
        """
        Determine shot type (2PT, 3PT, FT) from ESPN shot type text.

        Args:
            shot_type_text: ESPN shot type description

        Returns:
            '2PT', '3PT', or 'FT'
        """
        shot_lower = shot_type_text.lower()

        if 'three' in shot_lower or '3-pt' in shot_lower:
            return '3PT'
        elif 'free throw' in shot_lower:
            return 'FT'
        else:
            return '2PT'

    def calculate_shot_distance(self, x: int, y: int) -> int:
        """
        Calculate shot distance in feet from basket.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Distance in feet (approximate)
        """
        basket_x, basket_y = 25, 5
        distance_units = ((x - basket_x)**2 + (y - basket_y)**2)**0.5

        # Convert coordinate units to feet (approximate)
        # ESPN court: 50 units wide = 50 feet
        return int(distance_units)

    def save_to_database(self, game_id: str, shot_events: List[ESPNShotEvent]):
        """
        Save extracted shot events to shot_event_snapshots table.

        Args:
            game_id: ESPN game ID
            shot_events: List of shot events to save
        """
        if not self.conn:
            self.connect_db()

        cursor = self.conn.cursor()

        for shot in shot_events:
            # Determine shot type and zone
            shot_type = self.determine_shot_type(shot.shot_type_text)
            shot_zone = self.classify_shot_zone(
                shot.coordinate_x,
                shot.coordinate_y,
                shot.shot_type_text
            )
            shot_distance = self.calculate_shot_distance(
                shot.coordinate_x,
                shot.coordinate_y
            )

            # Note: event_number, score context, momentum indicators
            # will be populated later by linking to temporal snapshots
            cursor.execute("""
                INSERT OR IGNORE INTO shot_event_snapshots (
                    game_id, shot_id,
                    player_id, player_name, team_id,
                    period, game_clock, time_elapsed_seconds,
                    shot_made, shot_type, shot_distance,
                    shot_x, shot_y,
                    shot_zone,
                    score_diff, is_leading, is_clutch,
                    player_points_before, player_fgm_before, player_fga_before, player_fg_pct_before,
                    team_points_before, team_fgm_before, team_fga_before,
                    player_recent_points, player_recent_fg_pct, team_run
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                shot.game_id,
                shot.espn_play_id,
                shot.player_id,
                shot.player_name,
                shot.home_away,  # Temporary - will be resolved to team_id
                shot.period,
                None,  # game_clock - to be filled from PBP
                0,  # time_elapsed_seconds - to be filled
                shot.shot_made,
                shot_type,
                shot_distance,
                shot.coordinate_x,
                shot.coordinate_y,
                shot_zone,
                # Context fields - to be filled by linking to temporal snapshots
                None, None, None,  # score_diff, is_leading, is_clutch
                None, None, None, None,  # player stats before
                None, None, None,  # team stats before
                None, None, None  # momentum indicators
            ))

        self.conn.commit()
        logger.info(f"✓ Saved {len(shot_events)} shots from game {game_id}")

    def process_all_files(self, limit: Optional[int] = None):
        """
        Process all ESPN PBP JSON files in data directory.

        Args:
            limit: Maximum number of files to process (for testing)
        """
        json_files = list(self.data_dir.glob("*.json"))

        if limit:
            json_files = json_files[:limit]

        logger.info(f"Found {len(json_files)} ESPN PBP files")

        total_shots = 0
        games_with_shots = 0

        for i, file_path in enumerate(json_files, 1):
            if i % 1000 == 0:
                logger.info(f"Progress: {i}/{len(json_files)} files processed ({games_with_shots} games with shots, {total_shots} total shots)")

            game_id, shot_events = self.extract_shot_chart_from_file(file_path)

            if shot_events:
                self.save_to_database(game_id, shot_events)
                games_with_shots += 1
                total_shots += len(shot_events)

        logger.info(f"\n✓ COMPLETE")
        logger.info(f"  Processed: {len(json_files)} files")
        logger.info(f"  Games with shots: {games_with_shots}")
        logger.info(f"  Total shots: {total_shots}")
        logger.info(f"  Database: {self.db_path}")


def main():
    """Extract shot charts from all ESPN PBP files"""
    extractor = ESPNShotChartExtractor()

    try:
        # Create shot chart tables if they don't exist
        logger.info("Creating shot chart tables...")
        with open('sql/shot_chart_temporal_integration.sql', 'r') as f:
            schema = f.read()
            extractor.connect_db()
            extractor.conn.executescript(schema)
        logger.info("✓ Tables created")

        # Process all files (or use limit for testing)
        # extractor.process_all_files(limit=100)  # Test with 100 files
        extractor.process_all_files()  # Process all files

    finally:
        extractor.close()


if __name__ == "__main__":
    main()
