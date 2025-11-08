#!/usr/bin/env python3
"""
Master → raw_data ETL Migration Script

Migrates data from legacy master schema to production raw_data schema.

Usage:
    # Dry run (no writes)
    python scripts/migration/master_to_raw_data_etl.py --dry-run

    # Migrate 1000 games (test)
    python scripts/migration/master_to_raw_data_etl.py --limit 1000

    # Full migration
    python scripts/migration/master_to_raw_data_etl.py --full

    # Resume from checkpoint
    python scripts/migration/master_to_raw_data_etl.py --resume
"""

import sys
import os
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import psycopg2
from psycopg2.extras import execute_batch, Json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nba_simulator.config import config


class MigrationStats:
    """Track migration statistics"""

    def __init__(self):
        self.start_time = time.time()
        self.games_migrated = 0
        self.games_enriched = 0
        self.validations_migrated = 0
        self.errors = []
        self.checkpoints = []

    def elapsed(self) -> str:
        """Get elapsed time as string"""
        elapsed = time.time() - self.start_time
        mins = int(elapsed / 60)
        secs = int(elapsed % 60)
        return f"{mins}m {secs}s"

    def rate(self, count: int) -> float:
        """Calculate rows per second"""
        elapsed = time.time() - self.start_time
        return count / elapsed if elapsed > 0 else 0

    def summary(self) -> str:
        """Get summary string"""
        return f"""
Migration Statistics:
  Games migrated:      {self.games_migrated:,}
  Games enriched:      {self.games_enriched:,}
  Validations migrated: {self.validations_migrated:,}
  Errors:              {len(self.errors)}
  Elapsed time:        {self.elapsed()}
  Rate:                {self.rate(self.games_migrated):.1f} games/sec
"""


class MasterToRawDataETL:
    """ETL for migrating master schema to raw_data schema"""

    MIGRATION_VERSION = "1.0.0"
    CHECKPOINT_FILE = "migration_checkpoint.json"

    def __init__(
        self, dry_run: bool = False, verbose: bool = False, db_config: dict = None
    ):
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats = MigrationStats()
        self.conn = None
        self.cursor = None

        # Load database config
        if db_config:
            self.db_config = db_config
        else:
            self.db_config = config.load_database_config()

        self.log(f"Initialized ETL (dry_run={dry_run})")
        self.log(
            f"Database: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        )

    def log(self, message: str, level: str = "INFO"):
        """Log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️ ",
            "PROGRESS": "⏳",
        }.get(level, "  ")

        print(f"[{timestamp}] {prefix} {message}")

        if level == "ERROR":
            self.stats.errors.append(message)

    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            self.log("Connected to database")
        except Exception as e:
            self.log(f"Database connection failed: {e}", "ERROR")
            raise

    def disconnect(self):
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.log("Disconnected from database")

    def save_checkpoint(self, phase: str, data: Dict):
        """Save migration checkpoint"""
        checkpoint = {
            "phase": phase,
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "games_migrated": self.stats.games_migrated,
                "games_enriched": self.stats.games_enriched,
                "validations_migrated": self.stats.validations_migrated,
            },
            "data": data,
        }

        with open(self.CHECKPOINT_FILE, "w") as f:
            json.dump(checkpoint, f, indent=2)

        self.log(f"Checkpoint saved: {phase}")

    def load_checkpoint(self) -> Optional[Dict]:
        """Load migration checkpoint"""
        if not Path(self.CHECKPOINT_FILE).exists():
            return None

        with open(self.CHECKPOINT_FILE, "r") as f:
            checkpoint = json.load(f)

        self.log(f"Checkpoint loaded: {checkpoint['phase']}")
        return checkpoint

    # ========================================================================
    # Phase 1: Migrate Games
    # ========================================================================

    def migrate_games(self, limit: Optional[int] = None, offset: int = 0) -> int:
        """
        Migrate games from master.nba_games to raw_data.nba_games

        Args:
            limit: Maximum number of games to migrate (None = all)
            offset: Skip first N games

        Returns:
            Number of games migrated
        """
        self.log(f"Phase 1: Migrating games (limit={limit}, offset={offset})")

        # Get total count
        self.cursor.execute("SELECT COUNT(*) FROM master.nba_games")
        total_games = self.cursor.fetchone()[0]
        self.log(f"Total games in master: {total_games:,}")

        # Build query
        query = """
            SELECT
                game_id,
                COALESCE(source, 'ESPN') as source,
                season,
                game_date::date as game_date,
                created_at,
                updated_at,
                game_date as game_datetime,
                home_team,
                away_team,
                home_abbrev,
                away_abbrev,
                final_score_home,
                final_score_away
            FROM master.nba_games
            ORDER BY game_id
        """

        if offset > 0:
            query += f" OFFSET {offset}"
        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)
        games = self.cursor.fetchall()

        self.log(f"Fetched {len(games):,} games to migrate")

        # Batch insert
        batch_size = 1000
        batches = [games[i : i + batch_size] for i in range(0, len(games), batch_size)]

        migrated_count = 0

        for batch_idx, batch in enumerate(batches, 1):
            self.log(
                f"Processing batch {batch_idx}/{len(batches)} ({len(batch)} games)",
                "PROGRESS",
            )

            insert_data = []
            for game in batch:
                (
                    game_id,
                    source,
                    season,
                    game_date,
                    collected_at,
                    updated_at,
                    game_datetime,
                    home_team,
                    away_team,
                    home_abbrev,
                    away_abbrev,
                    home_score,
                    away_score,
                ) = game

                # Extract year from season string (e.g., "2001-02" → 2001)
                season_year = (
                    int(season.split("-")[0]) if season and "-" in season else None
                )

                # Build JSONB data
                data = {
                    "game_info": {
                        "game_id": game_id,
                        "game_date": (
                            game_datetime.isoformat() if game_datetime else None
                        ),
                        "season": season,  # Keep original season string in JSONB
                        "season_year": season_year,
                    },
                    "teams": {
                        "home": {
                            "name": home_team,
                            "abbreviation": home_abbrev,
                            "score": home_score,
                        },
                        "away": {
                            "name": away_team,
                            "abbreviation": away_abbrev,
                            "score": away_score,
                        },
                    },
                    "source_data": {"original_game_id": game_id, "source": source},
                }

                # Build JSONB metadata
                metadata = {
                    "collection": {
                        "collected_at": (
                            collected_at.isoformat() if collected_at else None
                        ),
                        "updated_at": updated_at.isoformat() if updated_at else None,
                        "source_system": source,
                    },
                    "migration": {
                        "migrated_at": datetime.now().isoformat(),
                        "migrated_from": "master.nba_games",
                        "migration_version": self.MIGRATION_VERSION,
                    },
                }

                insert_data.append(
                    (
                        game_id,
                        source,
                        season_year,
                        game_date,
                        collected_at,
                        updated_at,
                        Json(data),
                        Json(metadata),
                    )
                )

            # Insert batch
            if not self.dry_run:
                insert_query = """
                    INSERT INTO raw_data.nba_games (
                        game_id, source, season, game_date,
                        collected_at, updated_at, data, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (game_id) DO NOTHING
                """

                try:
                    execute_batch(self.cursor, insert_query, insert_data)
                    self.conn.commit()
                    migrated_count += len(batch)
                    self.stats.games_migrated += len(batch)

                    # Save checkpoint every 10 batches
                    if batch_idx % 10 == 0:
                        self.save_checkpoint(
                            "migrate_games",
                            {"offset": offset + migrated_count, "limit": limit},
                        )

                except Exception as e:
                    self.conn.rollback()
                    self.log(f"Batch insert failed: {e}", "ERROR")
                    raise
            else:
                migrated_count += len(batch)
                self.log(f"[DRY RUN] Would insert {len(batch)} games")

        self.log(f"Phase 1 complete: {migrated_count:,} games migrated", "SUCCESS")
        return migrated_count

    # ========================================================================
    # Phase 2: Enrich with Play Summaries
    # ========================================================================

    def enrich_with_plays(self, limit: Optional[int] = None) -> int:
        """
        Enrich games with play-by-play summaries

        Args:
            limit: Maximum number of games to enrich (None = all)

        Returns:
            Number of games enriched
        """
        self.log(f"Phase 2: Enriching games with play summaries (limit={limit})")

        # Get games to enrich
        query = """
            SELECT game_id
            FROM raw_data.nba_games
            WHERE NOT (metadata ? 'validation')
            ORDER BY game_id
        """

        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)
        game_ids = [row[0] for row in self.cursor.fetchall()]

        self.log(f"Found {len(game_ids):,} games to enrich")

        # Process in smaller batches (play aggregation is heavy)
        batch_size = 100
        batches = [
            game_ids[i : i + batch_size] for i in range(0, len(game_ids), batch_size)
        ]

        enriched_count = 0

        for batch_idx, batch in enumerate(batches, 1):
            self.log(
                f"Enriching batch {batch_idx}/{len(batches)} ({len(batch)} games)",
                "PROGRESS",
            )

            for game_id in batch:
                # Get play count
                self.cursor.execute(
                    "SELECT COUNT(*) FROM master.nba_plays WHERE game_id = %s",
                    (game_id,),
                )
                play_count = self.cursor.fetchone()[0]

                # Get max period
                self.cursor.execute(
                    """
                    SELECT MAX(period)
                    FROM master.nba_plays
                    WHERE game_id = %s
                """,
                    (game_id,),
                )
                max_period = self.cursor.fetchone()[0] or 4

                # Get play statistics by event type
                self.cursor.execute(
                    """
                    SELECT json_object_agg(event_type, cnt) as event_types
                    FROM (
                        SELECT event_type, COUNT(*) as cnt
                        FROM master.nba_plays
                        WHERE game_id = %s AND event_type IS NOT NULL
                        GROUP BY event_type
                    ) t
                """,
                    (game_id,),
                )

                result = self.cursor.fetchone()
                event_types = result[0] if result and result[0] else {}

                # Update game with play summary
                if not self.dry_run:
                    update_query = """
                        UPDATE raw_data.nba_games
                        SET
                            data = jsonb_set(
                                data,
                                '{play_by_play}',
                                %s::jsonb
                            ),
                            metadata = jsonb_set(
                                metadata,
                                '{validation}',
                                %s::jsonb
                            )
                        WHERE game_id = %s
                    """

                    play_summary = {
                        "total_plays": play_count,
                        "summary": {"periods": max_period, "event_types": event_types},
                    }

                    validation = {
                        "has_play_by_play": play_count > 0,
                        "play_count": play_count,
                        "validated_at": datetime.now().isoformat(),
                    }

                    try:
                        self.cursor.execute(
                            update_query,
                            (json.dumps(play_summary), json.dumps(validation), game_id),
                        )
                    except Exception as e:
                        self.log(f"Failed to enrich game {game_id}: {e}", "ERROR")
                        continue

                enriched_count += 1
                self.stats.games_enriched += 1

            # Commit batch
            if not self.dry_run:
                self.conn.commit()
                self.save_checkpoint("enrich_plays", {"enriched_count": enriched_count})

        self.log(f"Phase 2 complete: {enriched_count:,} games enriched", "SUCCESS")
        return enriched_count

    # ========================================================================
    # Phase 3: Migrate File Validations
    # ========================================================================

    def migrate_validations(self, limit: Optional[int] = None) -> int:
        """
        Migrate ESPN file validations to raw_data.nba_misc

        Args:
            limit: Maximum number of records to migrate (None = all)

        Returns:
            Number of records migrated
        """
        self.log(f"Phase 3: Migrating file validations (limit={limit})")

        # Get total count
        self.cursor.execute("SELECT COUNT(*) FROM master.espn_file_validation")
        total_validations = self.cursor.fetchone()[0]
        self.log(f"Total validations in master: {total_validations:,}")

        # Fetch validations
        query = """
            SELECT
                file_name,
                game_id,
                has_pbp_data,
                has_game_info,
                has_team_data,
                game_date,
                season,
                league,
                home_team,
                away_team,
                play_count,
                file_size_bytes,
                validation_timestamp,
                error_message
            FROM master.espn_file_validation
            ORDER BY file_name
        """

        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)
        validations = self.cursor.fetchall()

        self.log(f"Fetched {len(validations):,} validations to migrate")

        # Batch insert
        batch_size = 5000
        batches = [
            validations[i : i + batch_size]
            for i in range(0, len(validations), batch_size)
        ]

        migrated_count = 0

        for batch_idx, batch in enumerate(batches, 1):
            self.log(
                f"Processing batch {batch_idx}/{len(batches)} ({len(batch)} records)",
                "PROGRESS",
            )

            insert_data = []
            for validation in batch:
                (
                    file_name,
                    game_id,
                    has_pbp,
                    has_game_info,
                    has_team_data,
                    game_date,
                    season,
                    league,
                    home_team,
                    away_team,
                    play_count,
                    file_size,
                    validation_ts,
                    error_msg,
                ) = validation

                # Build JSONB data
                data = {
                    "file_info": {
                        "file_name": file_name,
                        "file_size_bytes": file_size,
                        "validation_timestamp": (
                            validation_ts.isoformat() if validation_ts else None
                        ),
                    },
                    "validation": {
                        "has_pbp_data": has_pbp,
                        "has_game_info": has_game_info,
                        "has_team_data": has_team_data,
                        "play_count": play_count,
                        "error_message": error_msg,
                    },
                    "game_reference": {
                        "game_id": game_id,
                        "season": season,
                        "league": league,
                        "game_date": game_date.isoformat() if game_date else None,
                        "home_team": home_team,
                        "away_team": away_team,
                    },
                }

                # Build JSONB metadata
                metadata = {
                    "migration": {
                        "migrated_at": datetime.now().isoformat(),
                        "migrated_from": "master.espn_file_validation",
                        "migration_version": self.MIGRATION_VERSION,
                    }
                }

                insert_data.append(
                    (
                        "ESPN",
                        "file_validation",
                        validation_ts,
                        Json(data),
                        Json(metadata),
                    )
                )

            # Insert batch
            if not self.dry_run:
                insert_query = """
                    INSERT INTO raw_data.nba_misc (
                        source, entity_type, collected_at, data, metadata
                    ) VALUES (%s, %s, %s, %s, %s)
                """

                try:
                    execute_batch(self.cursor, insert_query, insert_data)
                    self.conn.commit()
                    migrated_count += len(batch)
                    self.stats.validations_migrated += len(batch)

                except Exception as e:
                    self.conn.rollback()
                    self.log(f"Batch insert failed: {e}", "ERROR")
                    raise
            else:
                migrated_count += len(batch)
                self.log(f"[DRY RUN] Would insert {len(batch)} validations")

        self.log(
            f"Phase 3 complete: {migrated_count:,} validations migrated", "SUCCESS"
        )
        return migrated_count

    # ========================================================================
    # Main Migration
    # ========================================================================

    def run_migration(self, phases: List[str] = None, limit: Optional[int] = None):
        """
        Run full migration

        Args:
            phases: List of phases to run (['games', 'plays', 'validations'])
            limit: Limit for testing (applies to games only)
        """
        if phases is None:
            phases = ["games", "plays", "validations"]

        self.log(f"Starting migration (phases={phases}, limit={limit})")

        try:
            self.connect()

            if "games" in phases:
                self.migrate_games(limit=limit)

            if "plays" in phases:
                self.enrich_with_plays(limit=limit)

            if "validations" in phases:
                self.migrate_validations(limit=None if not limit else limit)

            self.log("Migration complete!", "SUCCESS")
            print(self.stats.summary())

        except Exception as e:
            self.log(f"Migration failed: {e}", "ERROR")
            raise
        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description="Migrate data from master schema to raw_data schema"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without writing to database",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--limit", type=int, help="Limit number of games to migrate (for testing)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full migration (all games, plays, validations)",
    )
    parser.add_argument(
        "--phases",
        nargs="+",
        choices=["games", "plays", "validations"],
        help="Specify which phases to run",
    )
    parser.add_argument(
        "--resume", action="store_true", help="Resume from last checkpoint"
    )
    parser.add_argument("--host", help="Database host (overrides config)")
    parser.add_argument("--port", type=int, help="Database port (overrides config)")
    parser.add_argument("--database", help="Database name (overrides config)")
    parser.add_argument("--user", help="Database user (overrides config)")
    parser.add_argument("--password", help="Database password (overrides config)")

    args = parser.parse_args()

    # Build database config from CLI args or environment
    db_config = None
    if any([args.host, args.port, args.database, args.user, args.password]):
        db_config = {
            "host": args.host or os.getenv("POSTGRES_HOST", "localhost"),
            "port": args.port or int(os.getenv("POSTGRES_PORT", "5432")),
            "database": args.database or os.getenv("POSTGRES_DB", "nba_simulator"),
            "user": args.user or os.getenv("POSTGRES_USER", "ryanranft"),
            "password": (
                args.password
                if args.password is not None
                else os.getenv("POSTGRES_PASSWORD", "")
            ),
        }

    # Create ETL instance
    etl = MasterToRawDataETL(
        dry_run=args.dry_run, verbose=args.verbose, db_config=db_config
    )

    # Determine phases
    phases = args.phases if args.phases else ["games", "plays", "validations"]

    # Determine limit
    limit = None
    if args.limit:
        limit = args.limit
    elif not args.full and not args.resume:
        # Default to 1000 for safety
        limit = 1000
        etl.log(
            "No --full flag specified, limiting to 1000 games for safety", "WARNING"
        )
        etl.log("Use --full for complete migration", "WARNING")

    # Run migration
    etl.run_migration(phases=phases, limit=limit)


if __name__ == "__main__":
    main()
