#!/usr/bin/env python3
"""
Plus/Minus Table Population Script

Populates plus/minus tables from existing player_snapshot_stats data:
- lineup_snapshots
- player_plus_minus_snapshots
- possession_metadata

Uses existing temporal snapshot data to generate lineup analysis and possession tracking.

Created: October 19, 2025
"""

import hashlib
import sqlite3
import psycopg2
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SnapshotData:
    """Represents a single snapshot from player_snapshot_stats"""
    snapshot_id: int
    game_id: str
    event_num: int
    quarter: int
    time_elapsed_seconds: int
    home_score: int
    away_score: int
    player_id: str
    player_name: str
    team_id: str
    plus_minus: int
    on_court: bool


class PlusMinusPopulator:
    """
    Populates plus/minus tables from existing snapshot data.

    Supports both SQLite (for testing) and PostgreSQL (for production).
    """

    def __init__(self, db_config: Dict[str, str], use_postgres: bool = False):
        """
        Initialize populator with database connection.

        Args:
            db_config: Database configuration
                SQLite: {'database': 'path/to/db.sqlite'}
                PostgreSQL: {'host': 'localhost', 'database': 'nba', ...}
            use_postgres: True for PostgreSQL, False for SQLite
        """
        self.use_postgres = use_postgres
        self.conn = self._connect(db_config)

        # Set row_factory for SQLite (PostgreSQL uses DictCursor instead)
        if not use_postgres:
            self.conn.row_factory = sqlite3.Row

    def _connect(self, config: Dict[str, str]):
        """Create database connection"""
        if self.use_postgres:
            return psycopg2.connect(**config)
        else:
            return sqlite3.connect(config['database'])

    # ========================================================================
    # Lineup Hash Calculation
    # ========================================================================

    def calculate_lineup_hash(self, player_ids: List[str]) -> str:
        """
        Calculate MD5 hash for a lineup (exactly 5 players).

        Args:
            player_ids: List of 5 player IDs

        Returns:
            MD5 hash string

        Raises:
            ValueError: If not exactly 5 players
        """
        if len(player_ids) != 5:
            raise ValueError(f"Lineup must have exactly 5 players, got {len(player_ids)}")

        # Sort alphabetically for consistent hash
        sorted_players = sorted(player_ids)

        # Create hash string
        lineup_string = '|'.join(sorted_players)

        # Calculate MD5
        return hashlib.md5(lineup_string.encode()).hexdigest()

    # ========================================================================
    # Data Loading
    # ========================================================================

    def load_game_snapshots(self, game_id: str) -> List[SnapshotData]:
        """
        Load all snapshots for a game from player_snapshot_stats.

        Args:
            game_id: Game identifier

        Returns:
            List of SnapshotData objects, sorted by event_num
        """
        cursor = self.conn.cursor()

        query = """
            SELECT
                p.snapshot_id,
                g.game_id,
                g.event_num,
                g.quarter,
                COALESCE(g.game_clock_seconds, 0) as time_elapsed_seconds,
                g.home_score,
                g.away_score,
                p.player_id,
                p.player_name,
                p.team_id,
                p.plus_minus,
                p.on_court
            FROM player_snapshot_stats p
            JOIN game_state_snapshots g ON p.snapshot_id = g.snapshot_id
            WHERE g.game_id = ?
            ORDER BY g.event_num, p.team_id, p.player_id
        """

        if self.use_postgres:
            query = query.replace('?', '%s')

        cursor.execute(query, (game_id,))

        snapshots = []
        for row in cursor.fetchall():
            snapshots.append(SnapshotData(
                snapshot_id=row[0],
                game_id=row[1],
                event_num=row[2],
                quarter=row[3],
                time_elapsed_seconds=row[4],
                home_score=row[5],
                away_score=row[6],
                player_id=row[7],
                player_name=row[8],
                team_id=row[9],
                plus_minus=row[10],
                on_court=bool(row[11])
            ))

        logger.info(f"Loaded {len(snapshots)} player snapshots for game {game_id}")
        return snapshots

    def get_teams_for_game(self, game_id: str) -> Tuple[str, str]:
        """
        Get home and away team IDs for a game.

        Args:
            game_id: Game identifier

        Returns:
            Tuple of (home_team_id, away_team_id)
        """
        cursor = self.conn.cursor()

        # Try to get from master_games first (if table exists)
        try:
            query = """
                SELECT home_team_id, away_team_id
                FROM master_games
                WHERE game_id = ?
            """

            if self.use_postgres:
                query = query.replace('?', '%s')

            cursor.execute(query, (game_id,))
            result = cursor.fetchone()

            if result:
                return result[0], result[1]
        except Exception:
            # Table doesn't exist or query failed, use fallback
            if self.use_postgres:
                self.conn.rollback()  # Rollback aborted transaction in PostgreSQL
            pass

        # Fallback: Get from player snapshots
        query = """
            SELECT DISTINCT team_id
            FROM player_snapshot_stats p
            JOIN game_state_snapshots g ON p.snapshot_id = g.snapshot_id
            WHERE g.game_id = ?
            LIMIT 2
        """

        if self.use_postgres:
            query = query.replace('?', '%s')

        cursor.execute(query, (game_id,))
        teams = [row[0] for row in cursor.fetchall()]

        if len(teams) == 2:
            # Assume first is home (could improve with actual home/away detection)
            return teams[0], teams[1]

        raise ValueError(f"Could not determine teams for game {game_id}")

    # ========================================================================
    # Lineup Extraction
    # ========================================================================

    def extract_lineups_from_snapshots(
        self,
        snapshots: List[SnapshotData],
        home_team_id: str,
        away_team_id: str
    ) -> List[Dict]:
        """
        Extract lineup data for each event from snapshots.

        Args:
            snapshots: List of SnapshotData objects
            home_team_id: Home team identifier
            away_team_id: Away team identifier

        Returns:
            List of lineup dictionaries for insertion
        """
        # Group snapshots by event
        events = defaultdict(list)
        for snap in snapshots:
            if snap.on_court:
                events[snap.event_num].append(snap)

        lineup_records = []
        possession_number = 1  # Will track possessions (simplified for now)

        for event_num in sorted(events.keys()):
            event_snapshots = events[event_num]

            # Get teams
            home_players = [s for s in event_snapshots if s.team_id == home_team_id]
            away_players = [s for s in event_snapshots if s.team_id == away_team_id]

            # Validate lineup sizes
            if len(home_players) != 5 or len(away_players) != 5:
                logger.warning(
                    f"Game {event_snapshots[0].game_id} event {event_num}: "
                    f"Invalid lineup (home={len(home_players)}, away={len(away_players)})"
                )
                continue

            # Create lineup records for both teams
            for team_players, team_id, opponent_id in [
                (home_players, home_team_id, away_team_id),
                (away_players, away_team_id, home_team_id)
            ]:
                # Sort players alphabetically
                sorted_players = sorted(team_players, key=lambda p: p.player_id)
                player_ids = [p.player_id for p in sorted_players]
                lineup_hash = self.calculate_lineup_hash(player_ids)

                # Get snapshot metadata
                snap = team_players[0]

                # Simple possession tracking: odd events = home, even = away
                offensive_possession = (event_num % 2 == 0) if team_id == home_team_id else (event_num % 2 == 1)

                lineup_records.append({
                    'game_id': snap.game_id,
                    'event_number': event_num,
                    'period': snap.quarter,
                    'time_elapsed_seconds': snap.time_elapsed_seconds,
                    'possession_number': possession_number,
                    'timestamp': datetime.now().isoformat(),
                    'team_id': team_id,
                    'opponent_team_id': opponent_id,
                    'home_team': team_id == home_team_id,  # Boolean for PostgreSQL compatibility
                    'player1_id': player_ids[0],
                    'player2_id': player_ids[1],
                    'player3_id': player_ids[2],
                    'player4_id': player_ids[3],
                    'player5_id': player_ids[4],
                    'lineup_hash': lineup_hash,
                    'team_score': snap.home_score if team_id == home_team_id else snap.away_score,
                    'opponent_score': snap.away_score if team_id == home_team_id else snap.home_score,
                    'plus_minus': snap.plus_minus,
                    'offensive_possession': offensive_possession
                })

            # Increment possession every ~10 events (simplified)
            if event_num % 10 == 0:
                possession_number += 1

        logger.info(f"Extracted {len(lineup_records)} lineup records")
        return lineup_records

    # ========================================================================
    # Player Plus/Minus Extraction
    # ========================================================================

    def extract_player_plus_minus(
        self,
        snapshots: List[SnapshotData],
        home_team_id: str,
        away_team_id: str
    ) -> List[Dict]:
        """
        Extract player plus/minus data for each event.

        Args:
            snapshots: List of SnapshotData objects
            home_team_id: Home team identifier
            away_team_id: Away team identifier

        Returns:
            List of player plus/minus dictionaries for insertion
        """
        # Track stints for each player
        player_stints = defaultdict(list)  # player_id -> list of (start_event, end_event)
        current_stints = {}  # player_id -> start_event

        # Group by event
        events = defaultdict(list)
        for snap in snapshots:
            events[snap.event_num].append(snap)

        player_records = []
        possession_number = 1

        for event_num in sorted(events.keys()):
            event_snapshots = events[event_num]

            for snap in event_snapshots:
                # Track stint start/end
                stint_id = None
                stint_number = None
                stint_start_event = None

                if snap.on_court:
                    # Player is on court
                    if snap.player_id not in current_stints:
                        # New stint starting
                        current_stints[snap.player_id] = event_num
                        player_stints[snap.player_id].append(event_num)

                    stint_number = len(player_stints[snap.player_id])
                    stint_start_event = current_stints[snap.player_id]
                    stint_id = f"{snap.game_id}:{snap.player_id}:{stint_number}"
                else:
                    # Player is on bench
                    if snap.player_id in current_stints:
                        # Stint ending
                        del current_stints[snap.player_id]

                player_records.append({
                    'game_id': snap.game_id,
                    'event_number': event_num,
                    'player_id': snap.player_id,
                    'period': snap.quarter,
                    'time_elapsed_seconds': snap.time_elapsed_seconds,
                    'possession_number': possession_number,
                    'timestamp': datetime.now().isoformat(),
                    'team_id': snap.team_id,
                    'opponent_team_id': away_team_id if snap.team_id == home_team_id else home_team_id,
                    'home_team': snap.team_id == home_team_id,  # Boolean for PostgreSQL compatibility
                    'on_court': snap.on_court,  # Already boolean
                    'team_score': snap.home_score if snap.team_id == home_team_id else snap.away_score,
                    'opponent_score': snap.away_score if snap.team_id == home_team_id else snap.home_score,
                    'plus_minus': snap.plus_minus,
                    'stint_id': stint_id,
                    'stint_number': stint_number,
                    'stint_start_event': stint_start_event,
                    'stint_end_event': None,  # Will be updated retroactively
                    'minutes_played_cumulative': 0.0,  # Calculate from events
                    'seconds_since_last_stint': None
                })

            # Increment possession every ~10 events
            if event_num % 10 == 0:
                possession_number += 1

        logger.info(f"Extracted {len(player_records)} player plus/minus records")
        return player_records

    # ========================================================================
    # Possession Metadata Extraction (Simplified)
    # ========================================================================

    def extract_possession_metadata(
        self,
        snapshots: List[SnapshotData],
        home_team_id: str,
        away_team_id: str,
        lineups: List[Dict]
    ) -> List[Dict]:
        """
        Extract possession metadata (simplified version).

        This is a simplified implementation. For production, you'd want
        to parse actual possession changes from play-by-play events.

        Args:
            snapshots: List of SnapshotData objects
            home_team_id: Home team identifier
            away_team_id: Away team identifier
            lineups: Lineup records for hash lookups

        Returns:
            List of possession dictionaries for insertion
        """
        # Group events into ~10-event possessions (simplified)
        events = defaultdict(list)
        for snap in snapshots:
            events[snap.event_num].append(snap)

        possession_records = []
        possession_number = 1
        start_event = 0

        sorted_events = sorted(events.keys())

        for i in range(0, len(sorted_events), 10):
            end_event = min(i + 10, len(sorted_events)) - 1
            start_event_num = sorted_events[i] if i < len(sorted_events) else sorted_events[-1]
            end_event_num = sorted_events[end_event] if end_event < len(sorted_events) else sorted_events[-1]

            start_snaps = events[start_event_num]
            end_snaps = events[end_event_num]

            if not start_snaps or not end_snaps:
                continue

            # Determine offensive team (alternating for now)
            offensive_team = home_team_id if possession_number % 2 == 1 else away_team_id
            defensive_team = away_team_id if offensive_team == home_team_id else home_team_id

            # Get lineup hashes from lineup records
            lineup_off = None
            lineup_def = None
            for lineup in lineups:
                if lineup['event_number'] == start_event_num:
                    if lineup['team_id'] == offensive_team:
                        lineup_off = lineup['lineup_hash']
                    if lineup['team_id'] == defensive_team:
                        lineup_def = lineup['lineup_hash']

            # Calculate points scored (simplified)
            start_score_off = start_snaps[0].home_score if offensive_team == home_team_id else start_snaps[0].away_score
            end_score_off = end_snaps[0].home_score if offensive_team == home_team_id else end_snaps[0].away_score
            points_scored = end_score_off - start_score_off

            possession_records.append({
                'game_id': start_snaps[0].game_id,
                'possession_number': possession_number,
                'period': start_snaps[0].quarter,
                'start_event_number': start_event_num,
                'end_event_number': end_event_num,
                'start_seconds': start_snaps[0].time_elapsed_seconds,
                'end_seconds': end_snaps[0].time_elapsed_seconds,
                'duration_seconds': end_snaps[0].time_elapsed_seconds - start_snaps[0].time_elapsed_seconds,
                'start_timestamp': datetime.now().isoformat(),
                'end_timestamp': datetime.now().isoformat(),
                'offensive_team_id': offensive_team,
                'defensive_team_id': defensive_team,
                'lineup_hash_offense': lineup_off,
                'lineup_hash_defense': lineup_def,
                'possession_result': 'made_shot' if points_scored > 0 else 'missed_shot',
                'points_scored': max(0, points_scored),
                'shot_type': '2pt' if points_scored == 2 else ('3pt' if points_scored == 3 else 'none'),
                'offensive_rebound': False,  # Boolean for PostgreSQL compatibility
                'second_chance': False,
                'fast_break': False,
                'in_the_paint': False,
                'defensive_rebound': False,
                'forced_turnover': False,
                'contested_shot': False,
                'points_per_possession': points_scored / 1.0 if points_scored >= 0 else 0.0,
                'expected_points': 1.0,  # Would calculate from shot location
                'score_differential_start': start_score_off - (start_snaps[0].away_score if offensive_team == home_team_id else start_snaps[0].home_score)
            })

            possession_number += 1

        logger.info(f"Extracted {len(possession_records)} possession records")
        return possession_records

    # ========================================================================
    # Database Insertion
    # ========================================================================

    def insert_lineup_snapshots(self, records: List[Dict]) -> int:
        """Insert lineup snapshot records"""
        if not records:
            return 0

        cursor = self.conn.cursor()

        query = """
            INSERT INTO lineup_snapshots (
                game_id, event_number, period, time_elapsed_seconds,
                possession_number, timestamp, team_id, opponent_team_id,
                home_team, player1_id, player2_id, player3_id, player4_id,
                player5_id, lineup_hash, team_score, opponent_score,
                plus_minus, offensive_possession
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """

        if self.use_postgres:
            query = query.replace('?', '%s')

        cursor.executemany(query, [
            (
                r['game_id'], r['event_number'], r['period'],
                r['time_elapsed_seconds'], r['possession_number'],
                r['timestamp'], r['team_id'], r['opponent_team_id'],
                r['home_team'], r['player1_id'], r['player2_id'],
                r['player3_id'], r['player4_id'], r['player5_id'],
                r['lineup_hash'], r['team_score'], r['opponent_score'],
                r['plus_minus'], r['offensive_possession']
            )
            for r in records
        ])

        self.conn.commit()
        logger.info(f"Inserted {len(records)} lineup snapshots")
        return len(records)

    def insert_player_plus_minus(self, records: List[Dict]) -> int:
        """Insert player plus/minus records"""
        if not records:
            return 0

        cursor = self.conn.cursor()

        query = """
            INSERT INTO player_plus_minus_snapshots (
                game_id, event_number, player_id, period,
                time_elapsed_seconds, possession_number, timestamp,
                team_id, opponent_team_id, home_team, on_court,
                team_score, opponent_score, plus_minus, stint_id,
                stint_number, stint_start_event, stint_end_event,
                minutes_played_cumulative, seconds_since_last_stint
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """

        if self.use_postgres:
            query = query.replace('?', '%s')

        cursor.executemany(query, [
            (
                r['game_id'], r['event_number'], r['player_id'],
                r['period'], r['time_elapsed_seconds'],
                r['possession_number'], r['timestamp'], r['team_id'],
                r['opponent_team_id'], r['home_team'], r['on_court'],
                r['team_score'], r['opponent_score'], r['plus_minus'],
                r['stint_id'], r['stint_number'], r['stint_start_event'],
                r['stint_end_event'], r['minutes_played_cumulative'],
                r['seconds_since_last_stint']
            )
            for r in records
        ])

        self.conn.commit()
        logger.info(f"Inserted {len(records)} player plus/minus records")
        return len(records)

    def insert_possession_metadata(self, records: List[Dict]) -> int:
        """Insert possession metadata records"""
        if not records:
            return 0

        cursor = self.conn.cursor()

        query = """
            INSERT INTO possession_metadata (
                game_id, possession_number, period, start_event_number,
                end_event_number, start_seconds, end_seconds,
                duration_seconds, start_timestamp, end_timestamp,
                offensive_team_id, defensive_team_id, lineup_hash_offense,
                lineup_hash_defense, possession_result, points_scored,
                shot_type, offensive_rebound, second_chance, fast_break,
                in_the_paint, defensive_rebound, forced_turnover,
                contested_shot, points_per_possession, expected_points,
                score_differential_start
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """

        if self.use_postgres:
            query = query.replace('?', '%s')

        cursor.executemany(query, [
            (
                r['game_id'], r['possession_number'], r['period'],
                r['start_event_number'], r['end_event_number'],
                r['start_seconds'], r['end_seconds'], r['duration_seconds'],
                r['start_timestamp'], r['end_timestamp'],
                r['offensive_team_id'], r['defensive_team_id'],
                r['lineup_hash_offense'], r['lineup_hash_defense'],
                r['possession_result'], r['points_scored'], r['shot_type'],
                r['offensive_rebound'], r['second_chance'], r['fast_break'],
                r['in_the_paint'], r['defensive_rebound'],
                r['forced_turnover'], r['contested_shot'],
                r['points_per_possession'], r['expected_points'],
                r['score_differential_start']
            )
            for r in records
        ])

        self.conn.commit()
        logger.info(f"Inserted {len(records)} possession metadata records")
        return len(records)

    # ========================================================================
    # Main Processing
    # ========================================================================

    def populate_game(self, game_id: str) -> Dict[str, int]:
        """
        Populate all plus/minus tables for a single game.

        Args:
            game_id: Game identifier

        Returns:
            Dictionary with counts of inserted records
        """
        logger.info(f"Processing game {game_id}")

        # Load snapshots
        snapshots = self.load_game_snapshots(game_id)
        if not snapshots:
            logger.warning(f"No snapshots found for game {game_id}")
            return {'lineups': 0, 'player_pm': 0, 'possessions': 0}

        # Get teams
        home_team_id, away_team_id = self.get_teams_for_game(game_id)
        logger.info(f"Teams: {home_team_id} (home) vs {away_team_id} (away)")

        # Extract data
        lineups = self.extract_lineups_from_snapshots(snapshots, home_team_id, away_team_id)
        player_pm = self.extract_player_plus_minus(snapshots, home_team_id, away_team_id)
        possessions = self.extract_possession_metadata(snapshots, home_team_id, away_team_id, lineups)

        # Insert data
        lineup_count = self.insert_lineup_snapshots(lineups)
        player_count = self.insert_player_plus_minus(player_pm)
        possession_count = self.insert_possession_metadata(possessions)

        return {
            'lineups': lineup_count,
            'player_pm': player_count,
            'possessions': possession_count
        }

    def populate_multiple_games(self, game_ids: List[str]) -> Dict[str, Dict[str, int]]:
        """
        Populate plus/minus tables for multiple games.

        Args:
            game_ids: List of game identifiers

        Returns:
            Dictionary mapping game_id to insert counts
        """
        results = {}

        for game_id in game_ids:
            try:
                counts = self.populate_game(game_id)
                results[game_id] = counts
                logger.info(
                    f"Game {game_id} complete: "
                    f"{counts['lineups']} lineups, "
                    f"{counts['player_pm']} player records, "
                    f"{counts['possessions']} possessions"
                )
            except Exception as e:
                logger.error(f"Error processing game {game_id}: {e}", exc_info=True)
                results[game_id] = {'error': str(e)}

        return results

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Populate plus/minus tables from snapshot data")
    parser.add_argument('--game-id', help='Single game ID to process')
    parser.add_argument('--game-ids', nargs='+', help='Multiple game IDs to process')
    parser.add_argument('--database', default='nba.db', help='Database path (SQLite)')
    parser.add_argument('--postgres', action='store_true', help='Use PostgreSQL')
    parser.add_argument('--pg-host', default='localhost', help='PostgreSQL host')
    parser.add_argument('--pg-database', default='nba', help='PostgreSQL database')
    parser.add_argument('--pg-user', default='postgres', help='PostgreSQL user')
    parser.add_argument('--pg-password', help='PostgreSQL password')

    args = parser.parse_args()

    # Configure database
    if args.postgres:
        db_config = {
            'host': args.pg_host,
            'database': args.pg_database,
            'user': args.pg_user,
            'password': args.pg_password or ''
        }
    else:
        db_config = {'database': args.database}

    # Create populator
    populator = PlusMinusPopulator(db_config, use_postgres=args.postgres)

    try:
        # Process games
        if args.game_id:
            results = populator.populate_game(args.game_id)
            print(f"\nResults for {args.game_id}:")
            print(f"  Lineups: {results['lineups']}")
            print(f"  Player +/-: {results['player_pm']}")
            print(f"  Possessions: {results['possessions']}")

        elif args.game_ids:
            results = populator.populate_multiple_games(args.game_ids)
            print(f"\nProcessed {len(results)} games:")
            for game_id, counts in results.items():
                if 'error' in counts:
                    print(f"  {game_id}: ERROR - {counts['error']}")
                else:
                    print(f"  {game_id}: {counts['lineups']} lineups, {counts['player_pm']} player records, {counts['possessions']} possessions")

        else:
            print("Please specify --game-id or --game-ids")

    finally:
        populator.close()