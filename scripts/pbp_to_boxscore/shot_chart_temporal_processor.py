#!/usr/bin/env python3
"""
Shot Chart Temporal Processor

Extracts shot events from play-by-play data and links them to temporal
box score snapshots, enabling spatial + temporal basketball analytics.

This enables queries like:
- "Show LeBron's shot chart in Q4 clutch moments"
- "Where did Curry shoot from when trailing by 5+?"
- "How did Kobe's shot selection change by quarter?"

Created: October 18, 2025
"""

import sqlite3
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ShotEvent:
    """Represents a single shot attempt with full context"""
    game_id: str
    event_number: int
    shot_id: str
    player_id: str
    player_name: str
    team_id: str

    # Game context
    period: int
    game_clock: str
    time_elapsed_seconds: int

    # Score context
    score_diff: int
    is_leading: bool
    is_clutch: bool

    # Shot details
    shot_made: bool
    shot_type: str  # '2PT', '3PT', 'FT'
    shot_distance: Optional[int]
    shot_x: Optional[int]
    shot_y: Optional[int]

    # Shot classification
    shot_zone: str
    shot_difficulty: Optional[str]
    is_assisted: bool
    assisting_player: Optional[str]

    # Player state
    player_points_before: int
    player_fgm_before: int
    player_fga_before: int
    player_fg_pct_before: float

    # Team state
    team_points_before: int
    team_fgm_before: int
    team_fga_before: int

    # Momentum
    player_recent_points: int
    player_recent_fg_pct: Optional[float]
    team_run: int


class ShotChartTemporalProcessor:
    """Process shot events and link to temporal snapshots"""

    def __init__(self, db_path: str = "/tmp/basketball_reference_boxscores.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def classify_shot_zone(self, shot_x: Optional[int], shot_y: Optional[int],
                          shot_type: str) -> str:
        """
        Classify shot location into zones.

        Court dimensions (NBA):
        - 50 feet wide (0-50)
        - 47 feet long (0-47)
        - Basket at (25, 5.25)
        - 3pt line: 23.75 feet at top, 22 feet in corners

        Zones:
        - paint: 0-5 feet from basket
        - short_mid: 5-10 feet
        - long_mid: 10-16 feet
        - corner_three: 3PT shots from corners
        - above_break_three: 3PT shots above break
        """
        if shot_type == 'FT':
            return 'free_throw'

        if shot_x is None or shot_y is None:
            return 'unknown'

        # Calculate distance from basket (25, 5.25)
        basket_x, basket_y = 25, 5.25
        distance = ((shot_x - basket_x)**2 + (shot_y - basket_y)**2)**0.5

        if shot_type == '3PT':
            # Corner three: near sidelines (x < 10 or x > 40)
            if shot_x < 10 or shot_x > 40:
                return 'corner_three'
            else:
                return 'above_break_three'

        elif shot_type == '2PT':
            if distance <= 5:
                return 'paint'
            elif distance <= 10:
                return 'short_mid'
            elif distance <= 16:
                return 'long_mid'
            else:
                return 'deep_two'

        return 'unknown'

    def parse_assist(self, description: str) -> Tuple[bool, Optional[str]]:
        """
        Parse assist information from PBP description.

        Examples:
        - "LeBron James makes 2-pt jump shot (Kyrie Irving assists)"
        - "Stephen Curry makes 3-pt jump shot"
        """
        assist_pattern = r'\(([A-Za-z\s\.]+)\s+assists?\)'
        match = re.search(assist_pattern, description)

        if match:
            return (True, match.group(1).strip())
        return (False, None)

    def calculate_momentum(self, player_id: str, game_id: str,
                          event_number: int) -> Tuple[int, Optional[float], int]:
        """
        Calculate momentum indicators:
        - Recent points (last 5 minutes)
        - Recent FG% (last 10 shots)
        - Team run (last 2 minutes)
        """
        cursor = self.conn.cursor()

        # Get recent points (last 5 minutes = 300 seconds)
        cursor.execute("""
            SELECT
                p.points - COALESCE(prev.points, 0) as recent_points
            FROM player_box_score_snapshots p
            LEFT JOIN player_box_score_snapshots prev
                ON p.game_id = prev.game_id
                AND p.player_id = prev.player_id
                AND prev.time_elapsed_seconds = p.time_elapsed_seconds - 300
            WHERE p.game_id = ? AND p.player_id = ?
            AND p.event_number = ?
        """, (game_id, player_id, event_number))

        row = cursor.fetchone()
        recent_points = row['recent_points'] if row and row['recent_points'] else 0

        # Get recent FG% (last 10 made shots)
        cursor.execute("""
            SELECT shot_made
            FROM shot_event_snapshots
            WHERE game_id = ? AND player_id = ?
            AND event_number < ?
            ORDER BY event_number DESC
            LIMIT 10
        """, (game_id, player_id, event_number))

        recent_shots = cursor.fetchall()
        if recent_shots:
            makes = sum(1 for s in recent_shots if s['shot_made'])
            recent_fg_pct = (makes / len(recent_shots)) * 100
        else:
            recent_fg_pct = None

        # Get team run (last 2 minutes)
        cursor.execute("""
            SELECT score_diff
            FROM team_box_score_snapshots
            WHERE game_id = ?
            AND event_number = ?
        """, (game_id, event_number))

        current_diff = cursor.fetchone()

        cursor.execute("""
            SELECT score_diff
            FROM team_box_score_snapshots
            WHERE game_id = ?
            AND time_elapsed_seconds <= (
                SELECT time_elapsed_seconds - 120
                FROM team_box_score_snapshots
                WHERE game_id = ? AND event_number = ?
            )
            ORDER BY event_number DESC
            LIMIT 1
        """, (game_id, game_id, event_number))

        prev_diff = cursor.fetchone()

        if current_diff and prev_diff:
            team_run = current_diff['score_diff'] - prev_diff['score_diff']
        else:
            team_run = 0

        return (recent_points, recent_fg_pct, team_run)

    def process_shot_event(self, pbp_event: Dict, player_snapshot: Dict,
                          team_snapshot: Dict) -> Optional[ShotEvent]:
        """
        Process a single shot event from PBP into a ShotEvent object.

        Args:
            pbp_event: Row from game_play_by_play
            player_snapshot: Player's cumulative stats before shot
            team_snapshot: Team's cumulative stats before shot
        """
        # Skip non-shot events
        if not pbp_event.get('shot_made') is not None:
            return None

        # Parse assist
        is_assisted, assisting_player = self.parse_assist(
            pbp_event.get('description', '')
        )

        # Classify shot zone
        shot_zone = self.classify_shot_zone(
            pbp_event.get('shot_x'),
            pbp_event.get('shot_y'),
            pbp_event.get('shot_type', '2PT')
        )

        # Calculate momentum
        recent_points, recent_fg_pct, team_run = self.calculate_momentum(
            pbp_event['primary_player'],
            pbp_event['game_id'],
            pbp_event['event_number']
        )

        # Determine if clutch (Q4, <5 min, <5 pt diff)
        time_elapsed = pbp_event.get('time_elapsed_seconds') or 0
        is_clutch = (
            pbp_event['quarter'] >= 4 and
            time_elapsed >= (48 * 60 - 5 * 60) and
            abs(team_snapshot.get('score_diff', 100)) <= 5
        )

        # Create shot event
        shot_event = ShotEvent(
            game_id=pbp_event['game_id'],
            event_number=pbp_event['event_number'],
            shot_id=f"{pbp_event['game_id']}_{pbp_event['event_number']}",
            player_id=pbp_event.get('primary_player', 'unknown'),
            player_name=pbp_event.get('primary_player', 'Unknown'),
            team_id=pbp_event.get('offensive_team', 'UNK'),

            period=pbp_event['quarter'],
            game_clock=pbp_event.get('time_remaining', '0:00'),
            time_elapsed_seconds=time_elapsed,

            score_diff=team_snapshot.get('score_diff', 0),
            is_leading=team_snapshot.get('is_leading', False),
            is_clutch=is_clutch,

            shot_made=pbp_event['shot_made'],
            shot_type=pbp_event.get('shot_type', '2PT'),
            shot_distance=pbp_event.get('shot_distance'),
            shot_x=pbp_event.get('shot_x'),
            shot_y=pbp_event.get('shot_y'),

            shot_zone=shot_zone,
            shot_difficulty=None,  # TODO: Calculate based on defender distance
            is_assisted=is_assisted,
            assisting_player=assisting_player,

            player_points_before=player_snapshot.get('points', 0),
            player_fgm_before=player_snapshot.get('fgm', 0),
            player_fga_before=player_snapshot.get('fga', 0),
            player_fg_pct_before=player_snapshot.get('fg_pct', 0.0),

            team_points_before=team_snapshot.get('points', 0),
            team_fgm_before=team_snapshot.get('fgm', 0),
            team_fga_before=team_snapshot.get('fga', 0),

            player_recent_points=recent_points,
            player_recent_fg_pct=recent_fg_pct,
            team_run=team_run
        )

        return shot_event

    def save_shot_event(self, shot: ShotEvent):
        """Save shot event to database"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO shot_event_snapshots (
                game_id, event_number, shot_id,
                player_id, player_name, team_id,
                period, game_clock, time_elapsed_seconds,
                score_diff, is_leading, is_clutch,
                shot_made, shot_type, shot_distance, shot_x, shot_y,
                shot_zone, shot_difficulty, is_assisted, assisting_player,
                player_points_before, player_fgm_before, player_fga_before, player_fg_pct_before,
                team_points_before, team_fgm_before, team_fga_before,
                player_recent_points, player_recent_fg_pct, team_run
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            shot.game_id, shot.event_number, shot.shot_id,
            shot.player_id, shot.player_name, shot.team_id,
            shot.period, shot.game_clock, shot.time_elapsed_seconds,
            shot.score_diff, shot.is_leading, shot.is_clutch,
            shot.shot_made, shot.shot_type, shot.shot_distance, shot.shot_x, shot.shot_y,
            shot.shot_zone, shot.shot_difficulty, shot.is_assisted, shot.assisting_player,
            shot.player_points_before, shot.player_fgm_before, shot.player_fga_before, shot.player_fg_pct_before,
            shot.team_points_before, shot.team_fgm_before, shot.team_fga_before,
            shot.player_recent_points, shot.player_recent_fg_pct, shot.team_run
        ))

        self.conn.commit()

    def process_game(self, game_id: str) -> int:
        """
        Process all shot events for a game.

        Returns number of shots processed.
        """
        cursor = self.conn.cursor()

        # Get all shot events from PBP
        cursor.execute("""
            SELECT *
            FROM game_play_by_play
            WHERE game_id = ?
            AND shot_made IS NOT NULL
            ORDER BY event_number
        """, (game_id,))

        shot_events = cursor.fetchall()
        shots_processed = 0

        logger.info(f"Processing {len(shot_events)} shot events for game {game_id}")

        for pbp_event in shot_events:
            event_num = pbp_event['event_number']
            player = pbp_event['primary_player']
            team = pbp_event['offensive_team']

            # Get player snapshot before this shot
            cursor.execute("""
                SELECT *
                FROM player_box_score_snapshots
                WHERE game_id = ? AND player_id = ? AND event_number = ?
            """, (game_id, player, event_num))

            player_snapshot = cursor.fetchone()

            # Get team snapshot before this shot
            cursor.execute("""
                SELECT *
                FROM team_box_score_snapshots
                WHERE game_id = ? AND team_id = ? AND event_number = ?
            """, (game_id, team, event_num))

            team_snapshot = cursor.fetchone()

            if not player_snapshot or not team_snapshot:
                logger.warning(f"Missing snapshot for event {event_num}, skipping")
                continue

            # Process shot event
            shot_event = self.process_shot_event(
                dict(pbp_event),
                dict(player_snapshot),
                dict(team_snapshot)
            )

            if shot_event:
                self.save_shot_event(shot_event)
                shots_processed += 1

        logger.info(f"✓ Processed {shots_processed} shots for game {game_id}")
        return shots_processed

    def get_available_games(self) -> List[str]:
        """Get list of games with PBP data"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT DISTINCT game_id
            FROM game_play_by_play
            WHERE shot_made IS NOT NULL
            ORDER BY game_id DESC
        """)

        games = [row['game_id'] for row in cursor.fetchall()]
        return games


def main():
    """Process shot events for all available games"""
    processor = ShotChartTemporalProcessor()

    try:
        # Create shot chart tables
        logger.info("Creating shot chart tables...")
        with open('sql/shot_chart_temporal_integration.sql', 'r') as f:
            schema = f.read()
            processor.conn.executescript(schema)

        # Get available games
        games = processor.get_available_games()
        logger.info(f"Found {len(games)} games with shot data")

        if not games:
            logger.warning("No games with shot data found. Run PBP scrapers first.")
            return

        # Process each game
        total_shots = 0
        for game_id in games:
            shots = processor.process_game(game_id)
            total_shots += shots

        logger.info(f"\n✓ COMPLETE")
        logger.info(f"  Total games processed: {len(games)}")
        logger.info(f"  Total shots processed: {total_shots}")
        logger.info(f"  Database: {processor.db_path}")

    finally:
        processor.close()


if __name__ == "__main__":
    main()
