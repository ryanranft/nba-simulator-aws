"""
Phase 0.0005: Possession Extraction - Database Extractor

This module handles database operations for possession extraction:
- Reading events from temporal_events table
- Running possession detection
- Writing possessions to temporal_possession_stats table
- Batch processing with checkpointing
- Progress tracking and error handling

Author: NBA Simulator AWS Team
Created: November 5, 2025
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

from .detector import PossessionDetector, PossessionBoundary
from .config import PossessionConfig

logger = logging.getLogger(__name__)


class PossessionExtractor:
    """
    Extracts possessions from temporal_events and writes to temporal_possession_stats.

    Features:
    - Batch processing for memory efficiency
    - Checkpoint/resume capability
    - Parallel processing support (future)
    - Progress tracking
    - Error handling with validation

    Usage:
        config = load_config('config/default_config.yaml')
        extractor = PossessionExtractor(config)
        extractor.extract_all_games()
    """

    def __init__(self, config: PossessionConfig):
        """
        Initialize extractor with configuration.

        Args:
            config: PossessionExtractionConfig object
        """
        self.config = config
        self.detector = PossessionDetector(config)
        self.conn = None
        self.cursor = None

        # Statistics tracking
        self.stats = {
            "games_processed": 0,
            "games_failed": 0,
            "possessions_extracted": 0,
            "events_processed": 0,
            "start_time": None,
            "end_time": None,
        }

    def connect(self) -> bool:
        """
        Establish database connection.

        Returns:
            True if successful, False otherwise
        """
        try:
            conn_string = self.config.database.connection_string
            self.conn = psycopg2.connect(conn_string)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            logger.info(f"Connected to database: {self.config.database.host}")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")

    def get_game_list(self, limit: Optional[int] = None) -> List[str]:
        """
        Get list of game IDs to process.

        Args:
            limit: Optional limit on number of games

        Returns:
            List of game_id strings
        """
        query = """
            SELECT DISTINCT game_id
            FROM temporal_events
            ORDER BY game_id
        """

        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)
        games = [row["game_id"] for row in self.cursor.fetchall()]
        logger.info(f"Found {len(games)} games to process")
        return games

    def get_events_for_game(self, game_id: str) -> List[Dict]:
        """
        Get all events for a specific game, sorted by (period, clock).

        Args:
            game_id: Game identifier

        Returns:
            List of event dictionaries
        """
        query = """
            SELECT
                event_id,
                game_id,
                quarter as period,
                FLOOR(game_clock_seconds / 60)::int as clock_minutes,
                (game_clock_seconds %% 60)::numeric(4,1) as clock_seconds,
                event_type,
                team_id,
                player_id,
                event_data->>'home_score' as home_score,
                event_data->>'away_score' as away_score,
                event_data->>'description' as description,
                event_data->>'season' as season,
                event_data->>'game_date' as game_date
            FROM temporal_events
            WHERE game_id = %s
            ORDER BY quarter ASC, game_clock_seconds DESC, event_id ASC
        """

        self.cursor.execute(query, (game_id,))
        raw_events = self.cursor.fetchall()

        # Convert to dictionaries with proper types
        events = []
        for row in raw_events:
            event = dict(row)
            # Convert scores to integers if present
            if event.get("home_score"):
                try:
                    event["home_score"] = int(event["home_score"])
                except:
                    event["home_score"] = 0
            if event.get("away_score"):
                try:
                    event["away_score"] = int(event["away_score"])
                except:
                    event["away_score"] = 0
            # Add season and game_date if available
            if not event.get("season"):
                event["season"] = 2013  # Default fallback
            if not event.get("game_date"):
                event["game_date"] = "2013-01-01"  # Default fallback

            events.append(event)

        logger.debug(f"Retrieved {len(events)} events for game {game_id}")
        return events

    def write_possessions(self, possessions: List[PossessionBoundary]) -> int:
        """
        Write possessions to database.

        Args:
            possessions: List of PossessionBoundary objects

        Returns:
            Number of possessions written
        """
        if not possessions:
            return 0

        insert_query = """
            INSERT INTO temporal_possession_stats (
                game_id, season, game_date, possession_number, period,
                offensive_team_id, defensive_team_id, home_team_id, away_team_id,
                start_clock_minutes, start_clock_seconds,
                end_clock_minutes, end_clock_seconds, duration_seconds,
                score_differential_start,
                home_score_start, away_score_start,
                home_score_end, away_score_end,
                points_scored, possession_result,
                field_goals_attempted, field_goals_made,
                three_pointers_attempted, three_pointers_made,
                free_throws_attempted, free_throws_made,
                points_per_possession, effective_field_goal_pct,
                start_event_id, end_event_id, event_count,
                is_clutch_time, is_garbage_time, is_fastbreak, has_timeout,
                validation_status, validation_notes
            ) VALUES (
                %(game_id)s, %(season)s, %(game_date)s, %(possession_number)s, %(period)s,
                %(offensive_team_id)s, %(defensive_team_id)s, %(home_team_id)s, %(away_team_id)s,
                %(start_clock_minutes)s, %(start_clock_seconds)s,
                %(end_clock_minutes)s, %(end_clock_seconds)s, %(duration_seconds)s,
                %(score_differential_start)s,
                %(home_score_start)s, %(away_score_start)s,
                %(home_score_end)s, %(away_score_end)s,
                %(points_scored)s, %(possession_result)s,
                %(field_goals_attempted)s, %(field_goals_made)s,
                %(three_pointers_attempted)s, %(three_pointers_made)s,
                %(free_throws_attempted)s, %(free_throws_made)s,
                %(points_per_possession)s, %(effective_field_goal_pct)s,
                %(start_event_id)s, %(end_event_id)s, %(event_count)s,
                %(is_clutch_time)s, %(is_garbage_time)s, %(is_fastbreak)s, %(has_timeout)s,
                %(validation_status)s, %(validation_notes)s
            )
        """

        # Convert PossessionBoundary objects to dictionaries
        possession_dicts = []
        for poss in possessions:
            # Handle None values for calculated fields
            try:
                ppp = poss.calculate_efficiency()
            except:
                ppp = None

            try:
                efg = poss.calculate_efg_percentage()
            except:
                efg = None

            poss_dict = {
                "game_id": poss.game_id,
                "season": poss.season,
                "game_date": poss.game_date,
                "possession_number": poss.possession_number,
                "period": poss.period,
                "offensive_team_id": poss.offensive_team_id,
                "defensive_team_id": poss.defensive_team_id,
                "home_team_id": poss.home_team_id,
                "away_team_id": poss.away_team_id,
                "start_clock_minutes": poss.start_clock_minutes,
                "start_clock_seconds": poss.start_clock_seconds,
                "end_clock_minutes": poss.end_clock_minutes,
                "end_clock_seconds": poss.end_clock_seconds,
                "duration_seconds": poss.duration_seconds,
                "score_differential_start": poss.score_differential_start,
                "home_score_start": poss.home_score_start,
                "away_score_start": poss.away_score_start,
                "home_score_end": poss.home_score_end,
                "away_score_end": poss.away_score_end,
                "points_scored": poss.points_scored,
                "possession_result": poss.possession_result,
                "field_goals_attempted": poss.field_goals_attempted,
                "field_goals_made": poss.field_goals_made,
                "three_pointers_attempted": poss.three_pointers_attempted,
                "three_pointers_made": poss.three_pointers_made,
                "free_throws_attempted": poss.free_throws_attempted,
                "free_throws_made": poss.free_throws_made,
                "points_per_possession": ppp,
                "effective_field_goal_pct": efg,
                "start_event_id": poss.start_event_id,
                "end_event_id": poss.end_event_id,
                "event_count": poss.event_count,
                "is_clutch_time": poss.is_clutch_time,
                "is_garbage_time": poss.is_garbage_time,
                "is_fastbreak": poss.is_fastbreak,
                "has_timeout": poss.has_timeout,
                "validation_status": poss.validation_status,
                "validation_notes": poss.validation_notes,
            }
            possession_dicts.append(poss_dict)

        # Batch insert
        try:
            self.cursor.executemany(insert_query, possession_dicts)
            self.conn.commit()
            logger.debug(f"Wrote {len(possessions)} possessions to database")
            return len(possessions)
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to write possessions: {e}")
            raise

    def process_game(self, game_id: str) -> Tuple[bool, int]:
        """
        Process a single game: extract events, detect possessions, write to DB.

        Args:
            game_id: Game identifier

        Returns:
            Tuple of (success: bool, num_possessions: int)
        """
        try:
            # 1. Get events
            events = self.get_events_for_game(game_id)
            if not events:
                logger.warning(f"No events found for game {game_id}")
                return False, 0

            self.stats["events_processed"] += len(events)

            # 2. Detect possessions
            possessions = self.detector.detect_possessions(events)
            if not possessions:
                logger.warning(f"No possessions detected for game {game_id}")
                return False, 0

            # 3. Write to database
            written = self.write_possessions(possessions)

            # 4. Update stats
            self.stats["possessions_extracted"] += written
            self.stats["games_processed"] += 1

            logger.info(f"Game {game_id}: {len(events)} events → {written} possessions")

            return True, written

        except Exception as e:
            # Rollback transaction on error to prevent "transaction aborted" state
            if self.conn:
                self.conn.rollback()
            logger.error(f"Failed to process game {game_id}: {e}", exc_info=True)
            self.stats["games_failed"] += 1
            return False, 0

    def extract_all_games(
        self, limit: Optional[int] = None, resume_from: Optional[str] = None
    ) -> Dict:
        """
        Extract possessions for all games in database.

        Args:
            limit: Optional limit on number of games to process
            resume_from: Optional game_id to resume from

        Returns:
            Dictionary with extraction statistics
        """
        self.stats["start_time"] = datetime.now()

        logger.info("Starting possession extraction for all games")

        # Get game list
        games = self.get_game_list(limit)

        # Resume from checkpoint if provided
        if resume_from and resume_from in games:
            resume_idx = games.index(resume_from)
            games = games[resume_idx:]
            logger.info(
                f"Resuming from game {resume_from} ({resume_idx} games skipped)"
            )

        total_games = len(games)

        # Process games
        for i, game_id in enumerate(games, 1):
            logger.info(f"Processing game {i}/{total_games}: {game_id}")

            success, num_possessions = self.process_game(game_id)

            if not success:
                logger.warning(f"Game {game_id} processing failed - continuing")

            # Progress reporting every 10 games
            if i % 10 == 0:
                self._log_progress(i, total_games)

        self.stats["end_time"] = datetime.now()

        # Final report
        self._log_final_report()

        return self.stats

    def _log_progress(self, current: int, total: int):
        """Log progress update."""
        pct = (current / total) * 100
        elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
        rate = current / elapsed if elapsed > 0 else 0

        logger.info(
            f"Progress: {current}/{total} ({pct:.1f}%) | "
            f"{self.stats['possessions_extracted']:,} possessions | "
            f"{rate:.1f} games/sec"
        )

    def _log_final_report(self):
        """Log final extraction report."""
        elapsed = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        logger.info("")
        logger.info("=" * 60)
        logger.info("Possession Extraction Complete")
        logger.info("=" * 60)
        logger.info(f"Total games processed: {self.stats['games_processed']:,}")
        logger.info(f"Total games failed: {self.stats['games_failed']:,}")
        logger.info(
            f"Total possessions extracted: {self.stats['possessions_extracted']:,}"
        )
        logger.info(f"Total events processed: {self.stats['events_processed']:,}")
        logger.info(f"Total time: {elapsed:.1f} seconds")
        logger.info(f"Average: {self.stats['games_processed']/elapsed:.1f} games/sec")
        logger.info("=" * 60)
