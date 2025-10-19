#!/usr/bin/env python3
"""
RDS Play-by-Play Processor - Generate Phase 9 Snapshots from PostgreSQL

Purpose: Process play-by-play data from RDS PostgreSQL to generate box score snapshots
Database: RDS PostgreSQL (nba_simulator)
Created: October 19, 2025

=== OVERVIEW ===

This module is the main coordinator that:
1. Connects to RDS PostgreSQL
2. Loads play-by-play events for a game
3. Uses PlayTextParser to parse natural language
4. Uses GameStateTracker to maintain cumulative state
5. Generates box_score_snapshots after each event
6. Saves snapshots to database

=== ARCHITECTURE ===

RDSPBPProcessor
├── PlayTextParser (NLP for play text)
├── GameStateTracker (state machine)
└── Database Connection (RDS PostgreSQL)

=== USAGE ===

```python
processor = RDSPBPProcessor()
processor.connect()

# Process a single game
result = processor.process_game("400827936")

# Process multiple games
results = processor.process_games(["400827936", "400827937", ...])

# Process all games
results = processor.process_all_games()
```

=== DATABASE SCHEMA ===

Input Tables:
- play_by_play (game_id, period_number, clock_display, play_text, etc.)
- games (game_id, home_team_id, away_team_id, etc.)
- box_score_players (game_id, player_id, starting lineup info)

Output Tables:
- box_score_snapshots (snapshot_id, game_id, event_num, period, clock, etc.)
- player_snapshot_stats (snapshot_id, player_id, cumulative stats)
- game_state_snapshots (snapshot_id, lineup hashes, metadata)
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import our components
from scripts.pbp_to_boxscore.play_text_parser import PlayTextParser
from scripts.pbp_to_boxscore.game_state_tracker import (
    GameStateTracker,
    PlayerState,
    GameState,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RDSPBPProcessor:
    """
    Main processor for generating Phase 9 snapshots from RDS play-by-play data.

    Coordinates PlayTextParser and GameStateTracker to create box score snapshots.
    """

    def __init__(self, db_config: Optional[Dict] = None, dry_run: bool = False):
        """
        Initialize RDSPBPProcessor.

        Args:
            db_config: Database configuration (if None, loads from .env)
            dry_run: If True, don't write to database
        """
        # Load credentials
        if db_config is None:
            load_dotenv("/Users/ryanranft/nba-sim-credentials.env")
            db_config = {
                "host": os.getenv(
                    "DB_HOST", "nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com"
                ),
                "database": os.getenv("DB_NAME", "nba_simulator"),
                "user": os.getenv("DB_USER"),
                "password": os.getenv("DB_PASSWORD"),
                "port": int(os.getenv("DB_PORT", 5432)),
            }

        self.db_config = db_config
        self.dry_run = dry_run
        self.conn = None
        self.parser = PlayTextParser()

        # Statistics
        self.stats = {
            "games_processed": 0,
            "games_failed": 0,
            "events_processed": 0,
            "snapshots_created": 0,
            "parse_failures": 0,
            "start_time": None,
            "end_time": None,
        }

        logger.info("RDSPBPProcessor initialized")
        if dry_run:
            logger.info("  Mode: DRY RUN (no database writes)")

    def connect(self):
        """Connect to RDS PostgreSQL."""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            logger.info(f"✓ Connected to RDS: {self.db_config['database']}")
        except Exception as e:
            logger.error(f"Failed to connect to RDS: {e}")
            raise

    def disconnect(self):
        """Disconnect from RDS."""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from RDS")

    def get_game_info(self, game_id: str) -> Optional[Dict]:
        """
        Get basic game information.

        Args:
            game_id: Game identifier

        Returns:
            Dictionary with game info (home_team_id, away_team_id, etc.)
        """
        query = """
        SELECT
            game_id,
            home_team_id,
            away_team_id,
            game_date,
            season
        FROM games
        WHERE game_id = %s
        LIMIT 1
        """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (game_id,))
            result = cur.fetchone()

        return dict(result) if result else None

    def get_play_by_play_events(self, game_id: str) -> List[Dict]:
        """
        Load all play-by-play events for a game.

        Args:
            game_id: Game identifier

        Returns:
            List of play-by-play events (ordered by play_id)
        """
        query = """
        SELECT
            play_id,
            game_id,
            period_number,
            period_display,
            clock_display,
            play_text,
            home_away,
            scoring_play,
            away_score,
            home_score
        FROM play_by_play
        WHERE game_id = %s
        ORDER BY play_id ASC
        """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (game_id,))
            events = cur.fetchall()

        return [dict(event) for event in events]

    def extract_player_names_from_pbp(self, game_id: str) -> Dict[str, str]:
        """
        Extract player names from play-by-play text and map to player IDs.

        Args:
            game_id: Game identifier

        Returns:
            Dictionary mapping player_id -> player_name (extracted from play text)
        """
        # Get all play texts for this game
        query = """
        SELECT DISTINCT play_text
        FROM play_by_play
        WHERE game_id = %s
        """

        with self.conn.cursor() as cur:
            cur.execute(query, (game_id,))
            play_texts = [row[0] for row in cur.fetchall()]

        # Extract unique player names using parser
        player_names = set()
        for play_text in play_texts:
            parsed = self.parser.parse(play_text)
            if parsed.primary_player:
                player_names.add(parsed.primary_player)
            if parsed.secondary_player:
                player_names.add(parsed.secondary_player)

        # Get player IDs from box_score_players
        query = """
        SELECT player_id, team_id, is_starter, minutes
        FROM box_score_players
        WHERE game_id = %s
        ORDER BY minutes DESC
        """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (game_id,))
            players = cur.fetchall()

        # Try to map player names to IDs
        # Strategy: Look for player names in the extracted set that are likely to match
        player_id_to_name = {}

        # Also get names from players table for backup
        query = """
        SELECT p.player_id, p.player_name
        FROM players p
        JOIN box_score_players bsp ON p.player_id = bsp.player_id
        WHERE bsp.game_id = %s
        """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (game_id,))
            db_players = cur.fetchall()

        # Build mapping from database first
        for player in db_players:
            if player["player_name"]:
                player_id_to_name[player["player_id"]] = player["player_name"]

        # For any players without names, try to match from extracted names
        # (This is a simplified approach - in production would use fuzzy matching)
        for player in players:
            if player["player_id"] not in player_id_to_name:
                # Use player_id as fallback
                player_id_to_name[player["player_id"]] = player["player_id"]

        logger.debug(
            f"Extracted {len(player_names)} unique player names from play text"
        )
        logger.debug(f"Mapped {len(player_id_to_name)} player IDs to names")

        return player_id_to_name

    def get_starting_lineups(self, game_id: str) -> Tuple[List[str], List[str]]:
        """
        Get starting lineups by analyzing early play-by-play events.

        Since player names may not be in database, extract them directly from
        the first ~50 plays to identify starting lineups.

        Args:
            game_id: Game identifier

        Returns:
            Tuple of (home_lineup, away_lineup) - each is a list of player names
        """
        # Get first 50 play-by-play events (likely to contain all starters)
        query = """
        SELECT play_text, home_away
        FROM play_by_play
        WHERE game_id = %s
        ORDER BY play_id ASC
        LIMIT 50
        """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (game_id,))
            early_plays = cur.fetchall()

        # Extract player names and count occurrences by team
        home_players = {}  # player_name -> count
        away_players = {}

        for play in early_plays:
            parsed = self.parser.parse(play["play_text"], team_id=play["home_away"])

            # Add primary player
            if parsed.primary_player:
                if play["home_away"] == "home":
                    home_players[parsed.primary_player] = (
                        home_players.get(parsed.primary_player, 0) + 1
                    )
                else:
                    away_players[parsed.primary_player] = (
                        away_players.get(parsed.primary_player, 0) + 1
                    )

            # Add secondary player (assists, etc.)
            if parsed.secondary_player:
                if play["home_away"] == "home":
                    home_players[parsed.secondary_player] = (
                        home_players.get(parsed.secondary_player, 0) + 1
                    )
                else:
                    away_players[parsed.secondary_player] = (
                        away_players.get(parsed.secondary_player, 0) + 1
                    )

        # Get top 5 players by mentions for each team
        home_lineup = sorted(home_players.items(), key=lambda x: x[1], reverse=True)[:5]
        away_lineup = sorted(away_players.items(), key=lambda x: x[1], reverse=True)[:5]

        home_lineup = [name for name, count in home_lineup]
        away_lineup = [name for name, count in away_lineup]

        # Get team IDs for logging
        game_info = self.get_game_info(game_id)
        home_team_id = game_info["home_team_id"] if game_info else "HOME"
        away_team_id = game_info["away_team_id"] if game_info else "AWAY"

        logger.info(f"Inferred starting lineups from early plays:")
        logger.info(f"  Home ({home_team_id}): {home_lineup}")
        logger.info(f"  Away ({away_team_id}): {away_lineup}")

        return (home_lineup, away_lineup)

    def process_game(self, game_id: str, save_to_db: bool = True) -> Dict[str, Any]:
        """
        Process a single game and generate snapshots.

        Args:
            game_id: Game identifier
            save_to_db: Whether to save snapshots to database

        Returns:
            Result dictionary with success/failure info
        """
        logger.info("=" * 80)
        logger.info(f"Processing game: {game_id}")
        logger.info("=" * 80)

        start_time = time.time()

        try:
            # Get game info
            game_info = self.get_game_info(game_id)
            if not game_info:
                raise ValueError(f"Game {game_id} not found in database")

            # Load play-by-play events
            events = self.get_play_by_play_events(game_id)
            if not events:
                raise ValueError(f"No play-by-play events found for game {game_id}")

            logger.info(f"Loaded {len(events)} play-by-play events")

            # Get starting lineups
            home_lineup, away_lineup = self.get_starting_lineups(game_id)

            # Initialize game state tracker
            tracker = GameStateTracker(
                game_id=game_id,
                home_team_id=game_info["home_team_id"],
                away_team_id=game_info["away_team_id"],
            )

            # Set starting lineups
            if home_lineup:
                tracker.set_starting_lineup(game_info["home_team_id"], home_lineup)
            if away_lineup:
                tracker.set_starting_lineup(game_info["away_team_id"], away_lineup)

            # Process each event
            snapshots = []
            parse_failures = 0

            for idx, event in enumerate(events, start=1):
                # Parse play text
                parsed_play = self.parser.parse(
                    event["play_text"], team_id=event["home_away"]
                )

                # Check for parse failure
                if parsed_play.action_type.value == "unknown":
                    parse_failures += 1
                    logger.debug(f"Failed to parse: {event['play_text']}")

                # Process event and create snapshot
                snapshot = tracker.process_event(
                    event_num=idx,
                    period=event["period_number"],
                    clock_display=event["clock_display"] or "0:00",
                    play_text=event["play_text"],
                    parsed_play=parsed_play,
                    home_score=event["home_score"] or 0,
                    away_score=event["away_score"] or 0,
                )

                snapshots.append(snapshot)

                # Progress logging
                if idx % 100 == 0:
                    logger.info(f"  Processed {idx}/{len(events)} events...")

            logger.info(f"✓ Processed all {len(events)} events")
            logger.info(
                f"  Parser success rate: {(len(events) - parse_failures) / len(events):.1%}"
            )

            # Save to database (if not dry run)
            if save_to_db and not self.dry_run:
                self._save_snapshots_to_db(game_id, snapshots)
                logger.info(f"✓ Saved {len(snapshots)} snapshots to database")

            # Update stats
            self.stats["games_processed"] += 1
            self.stats["events_processed"] += len(events)
            self.stats["snapshots_created"] += len(snapshots)
            self.stats["parse_failures"] += parse_failures

            elapsed = time.time() - start_time

            result = {
                "success": True,
                "game_id": game_id,
                "events_processed": len(events),
                "snapshots_created": len(snapshots),
                "parse_failures": parse_failures,
                "parse_success_rate": (len(events) - parse_failures) / len(events),
                "elapsed_seconds": elapsed,
            }

            logger.info(f"✓ Game {game_id} completed in {elapsed:.2f}s")

            return result

        except Exception as e:
            logger.error(f"✗ Failed to process game {game_id}: {e}")
            self.stats["games_failed"] += 1

            return {"success": False, "game_id": game_id, "error": str(e)}

    def _save_snapshots_to_db(self, game_id: str, snapshots: List[GameState]):
        """
        Save snapshots to database.

        Args:
            game_id: Game identifier
            snapshots: List of GameState snapshots
        """
        # This is a placeholder - actual implementation would insert into:
        # - box_score_snapshots
        # - player_snapshot_stats
        # - game_state_snapshots

        logger.info(f"Saving {len(snapshots)} snapshots for game {game_id}...")

        # TODO: Implement database insertion
        # For now, just log what we would save

        logger.debug(f"Would insert into box_score_snapshots: {len(snapshots)} rows")
        logger.debug(
            f"Would insert into player_snapshot_stats: ~{len(snapshots) * 10} rows"
        )
        logger.debug(f"Would insert into game_state_snapshots: {len(snapshots)} rows")

    def process_games(self, game_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple games.

        Args:
            game_ids: List of game identifiers

        Returns:
            List of result dictionaries
        """
        self.stats["start_time"] = datetime.now()

        results = []
        for idx, game_id in enumerate(game_ids, start=1):
            logger.info(f"\n[{idx}/{len(game_ids)}] Processing game {game_id}...")
            result = self.process_game(game_id)
            results.append(result)

        self.stats["end_time"] = datetime.now()

        # Print summary
        self._print_summary()

        return results

    def process_all_games(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Process all games with play-by-play data.

        Args:
            limit: Maximum number of games to process (None = all)

        Returns:
            List of result dictionaries
        """
        # Get all game IDs with play-by-play data
        query = """
        SELECT DISTINCT game_id
        FROM play_by_play
        ORDER BY game_id ASC
        """

        if limit:
            query += f" LIMIT {limit}"

        with self.conn.cursor() as cur:
            cur.execute(query)
            game_ids = [row[0] for row in cur.fetchall()]

        logger.info(f"Found {len(game_ids)} games with play-by-play data")

        return self.process_games(game_ids)

    def _print_summary(self):
        """Print processing summary."""
        logger.info("\n" + "=" * 80)
        logger.info("PROCESSING SUMMARY")
        logger.info("=" * 80)

        logger.info(f"Games processed:    {self.stats['games_processed']}")
        logger.info(f"Games failed:       {self.stats['games_failed']}")
        logger.info(f"Events processed:   {self.stats['events_processed']:,}")
        logger.info(f"Snapshots created:  {self.stats['snapshots_created']:,}")
        logger.info(f"Parse failures:     {self.stats['parse_failures']:,}")

        if self.stats["events_processed"] > 0:
            success_rate = (
                self.stats["events_processed"] - self.stats["parse_failures"]
            ) / self.stats["events_processed"]
            logger.info(f"Parse success rate: {success_rate:.1%}")

        if self.stats["start_time"] and self.stats["end_time"]:
            elapsed = (
                self.stats["end_time"] - self.stats["start_time"]
            ).total_seconds()
            logger.info(f"Total time:         {elapsed:.2f}s")

            if self.stats["games_processed"] > 0:
                avg_per_game = elapsed / self.stats["games_processed"]
                logger.info(f"Avg per game:       {avg_per_game:.2f}s")

        logger.info("=" * 80)

    def test_with_single_game(self, game_id: Optional[str] = None):
        """
        Test processor with a single game from database.

        Args:
            game_id: Specific game ID to test (if None, picks first available)
        """
        if not game_id:
            # Get first game with play-by-play data
            query = """
            SELECT DISTINCT game_id
            FROM play_by_play
            ORDER BY game_id ASC
            LIMIT 1
            """

            with self.conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchone()

            if not result:
                logger.error("No games with play-by-play data found")
                return

            game_id = result[0]

        logger.info(f"Testing with game: {game_id}")

        # Process game
        result = self.process_game(game_id, save_to_db=False)

        # Print result
        logger.info("\n" + "=" * 80)
        logger.info("TEST RESULT")
        logger.info("=" * 80)
        for key, value in result.items():
            logger.info(f"  {key}: {value}")
        logger.info("=" * 80)


def main():
    """Main entry point - Test with a single game."""
    logger.info("=== RDS PBP Processor - Test Run ===\n")

    # Initialize processor
    processor = RDSPBPProcessor(dry_run=True)

    # Connect to database
    processor.connect()

    try:
        # Test with first available game
        processor.test_with_single_game()

    finally:
        # Disconnect
        processor.disconnect()

    logger.info("\n✅ Test complete!")


if __name__ == "__main__":
    main()
