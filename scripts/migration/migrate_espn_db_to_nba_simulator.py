#!/usr/bin/env python3
"""
Migrate ESPN Database to nba_simulator.espn Schema

This script migrates data from the standalone ESPN PostgreSQL database to the
nba_simulator.espn schema using SQL queries with JSON file lookups for accurate
seasonType values.

Source: espn database (localhost)
Target: nba_simulator database (localhost)

Usage:
    python scripts/migration/migrate_espn_db_to_nba_simulator.py \
        --source-db espn \
        --target-db nba_simulator \
        --json-path /Users/ryanranft/0espn/data/nba/nba_box_score \
        --batch-size 1000

Options:
    --source-db         Source database name (default: espn)
    --target-db         Target database name (default: nba_simulator)
    --json-path         Path to ESPN JSON files (default: /Users/ryanranft/0espn/data/nba/nba_box_score)
    --batch-size        Batch size for processing (default: 1000)
    --dry-run           Preview without inserting
    --skip-games        Skip games migration
    --skip-plays        Skip plays migration
    --skip-schedules    Skip schedules migration
    --skip-team-stats   Skip team stats migration

Expected output:
- espn.espn_games: 44,827 rows
- espn.espn_team_stats: 89,654 rows
- espn.espn_plays: 14,114,618 rows
- espn.espn_schedules: 6,917 rows

Time estimate: 30-45 minutes
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import execute_batch, Json, RealDictCursor

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ESPNDatabaseMigrator:
    """Migrate data from ESPN database to nba_simulator.espn schema."""

    def __init__(
        self,
        source_host: str = "localhost",
        source_db: str = "espn",
        source_user: str = "ryanranft",
        target_host: str = "localhost",
        target_db: str = "nba_simulator",
        target_user: str = "ryanranft",
        json_path: str = "/Users/ryanranft/0espn/data/nba/nba_box_score",
        dry_run: bool = False,
    ):
        """
        Initialize migrator.

        Args:
            source_host: ESPN database host
            source_db: ESPN database name
            source_user: ESPN database user
            target_host: Target database host
            target_db: Target database name
            target_user: Target database user
            json_path: Path to ESPN JSON files directory
            dry_run: If True, preview without inserting
        """
        self.source_config = {
            "host": source_host,
            "database": source_db,
            "user": source_user,
            "password": "",  # Local trust authentication
        }

        self.target_config = {
            "host": target_host,
            "database": target_db,
            "user": target_user,
            "password": "",
        }

        self.json_path = Path(json_path)
        self.dry_run = dry_run

        # Statistics
        self.stats = {
            "games_migrated": 0,
            "games_updated": 0,
            "games_inserted": 0,
            "games_failed": 0,
            "season_type_from_json": 0,
            "season_type_from_date": 0,
            "season_type_failed": 0,
            "team_stats_inserted": 0,
            "plays_migrated": 0,
            "schedules_migrated": 0,
        }

        # Connections
        self.source_conn = None
        self.target_conn = None

        logger.info(f"Initialized ESPNDatabaseMigrator")
        logger.info(f"  Source: {source_db}@{source_host}")
        logger.info(f"  Target: {target_db}@{target_host}")
        logger.info(f"  JSON path: {json_path}")
        logger.info(f"  Dry run: {dry_run}")

    def connect(self):
        """Establish database connections."""
        try:
            self.source_conn = psycopg2.connect(**self.source_config)
            logger.info(f"✓ Connected to source: {self.source_config['database']}")
        except Exception as e:
            logger.error(f"Failed to connect to source database: {e}")
            raise

        try:
            self.target_conn = psycopg2.connect(**self.target_config)
            logger.info(f"✓ Connected to target: {self.target_config['database']}")
        except Exception as e:
            logger.error(f"Failed to connect to target database: {e}")
            raise

    def close(self):
        """Close database connections."""
        if self.source_conn:
            self.source_conn.close()
            logger.info("Closed source connection")

        if self.target_conn:
            self.target_conn.close()
            logger.info("Closed target connection")

    def get_season_type(
        self, game_id: str, game_date: datetime
    ) -> Tuple[Optional[int], str]:
        """
        Get season_type for a game.

        First tries to load from JSON file for 100% accuracy.
        Falls back to date-based inference if JSON not found.

        Args:
            game_id: ESPN game ID
            game_date: Game date

        Returns:
            Tuple of (season_type, source)
            season_type: 1=Preseason, 2=Regular, 3=Playoffs, 5=Play-In
            source: 'json' or 'date_inference' or 'failed'
        """
        # Try JSON file first
        json_file = self.json_path / f"{game_id}.json"

        if json_file.exists():
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                    season_type = (
                        data.get("page", {})
                        .get("content", {})
                        .get("gamepackage", {})
                        .get("gmStrp", {})
                        .get("seasonType")
                    )

                    if season_type in (1, 2, 3, 5):
                        return season_type, "json"
            except Exception as e:
                logger.warning(f"Error reading JSON for {game_id}: {e}")

        # Fallback to date inference
        try:
            season_type = self._infer_season_type_from_date(game_date)
            return season_type, "date_inference"
        except Exception as e:
            logger.error(f"Failed to infer season_type for {game_id}: {e}")
            return None, "failed"

    def _infer_season_type_from_date(self, game_date: datetime) -> int:
        """
        Infer season_type from game date.

        Based on analysis from ESPN_SEASON_TYPE_ENCODING.md:
        - Code 1: Preseason (Early-mid October)
        - Code 2: Regular Season (Late Oct - Mid Apr, includes All-Star)
        - Code 3: Playoffs (Mid Apr - Mid Jun)
        - Code 5: Play-In Tournament (Mid-April, 2020+ only)

        Args:
            game_date: Game datetime

        Returns:
            season_type: 1, 2, 3, or 5
        """
        month = game_date.month
        day = game_date.day
        year = game_date.year

        # Preseason: Early-mid October (before ~Oct 20)
        if month == 10 and day < 20:
            return 1

        # Play-In Tournament: Mid-April (2020+)
        # Typically April 11-20
        if year >= 2020 and month == 4 and 11 <= day <= 20:
            return 5

        # Playoffs: Mid-April through mid-June
        # April 16+ OR May OR June 1-20
        if month == 6 or month == 5 or (month == 4 and day > 15):
            return 3

        # Regular Season: Everything else
        # Late Oct - Mid Apr (including All-Star game in February)
        return 2

    def build_game_jsonb(
        self, game_row: Dict, player_rows: List[Dict], play_count: int, season_type: int
    ) -> Dict:
        """
        Build full JSONB structure for espn_games matching existing enriched format.

        Args:
            game_row: Row from nba_box_score_teams table
            player_rows: Rows from nba_box_score_players table
            play_count: Number of plays for this game
            season_type: Season type (1, 2, 3, or 5)

        Returns:
            Complete JSONB dict matching existing enrichment format
        """
        # Extract game date and calculate season
        game_date = game_row["game_date"]
        if game_date.month >= 10:
            season_year = game_date.year
        else:
            season_year = game_date.year - 1

        # Build player arrays grouped by team
        home_players = []
        away_players = []

        for p in player_rows:
            player_data = {
                "player_id": str(p.get("player_id", "")),
                "name": p.get("player_name", ""),
                "position": p.get("position", ""),
                "minutes": p.get("minutes", ""),
                "field_goals": p.get("field_goals", ""),
                "three_pointers": p.get("three_pointers", ""),
                "free_throws": p.get("free_throws", ""),
                "rebounds": p.get("total_rebounds", 0),
                "assists": p.get("assists", 0),
                "steals": p.get("steals", 0),
                "blocks": p.get("blocks", 0),
                "turnovers": p.get("turnovers", 0),
                "fouls": p.get("fouls", 0),
                "points": p.get("points", 0),
                "plus_minus": p.get("plus_minus", ""),
            }

            if p.get("team_abbrev") == game_row["home_team_abbrev"]:
                home_players.append(player_data)
            else:
                away_players.append(player_data)

        # Construct full JSONB structure
        enriched_data = {
            "teams": {
                "home": {
                    "name": game_row[
                        "home_team_abbrev"
                    ],  # Will be full name in real data
                    "abbreviation": game_row["home_team_abbrev"],
                    "score": game_row.get("home_team_score", 0),
                    "stats": {
                        "field_goals": game_row.get("home_team_field_goals", ""),
                        "field_goals_pct": float(
                            game_row.get("home_team_field_goals_pct", 0) or 0
                        ),
                        "three_pointers": game_row.get("home_team_three_pointers", ""),
                        "three_pointers_pct": float(
                            game_row.get("home_team_three_pointers_pct", 0) or 0
                        ),
                        "free_throws": game_row.get("home_team_free_throws", ""),
                        "free_throws_pct": float(
                            game_row.get("home_team_free_throws_pct", 0) or 0
                        ),
                        "offensive_rebounds": game_row.get(
                            "home_team_offensive_rebounds", 0
                        ),
                        "defensive_rebounds": game_row.get(
                            "home_team_defensive_rebounds", 0
                        ),
                        "total_rebounds": game_row.get("home_team_total_rebounds", 0),
                        "assists": game_row.get("home_team_assists", 0),
                        "steals": game_row.get("home_team_steals", 0),
                        "blocks": game_row.get("home_team_blocks", 0),
                        "turnovers": game_row.get("home_team_turnovers", 0),
                        "fouls": game_row.get("home_team_fouls", 0),
                    },
                },
                "away": {
                    "name": game_row["away_team_abbrev"],
                    "abbreviation": game_row["away_team_abbrev"],
                    "score": game_row.get("away_team_score", 0),
                    "stats": {
                        "field_goals": game_row.get("away_team_field_goals", ""),
                        "field_goals_pct": float(
                            game_row.get("away_team_field_goals_pct", 0) or 0
                        ),
                        "three_pointers": game_row.get("away_team_three_pointers", ""),
                        "three_pointers_pct": float(
                            game_row.get("away_team_three_pointers_pct", 0) or 0
                        ),
                        "free_throws": game_row.get("away_team_free_throws", ""),
                        "free_throws_pct": float(
                            game_row.get("away_team_free_throws_pct", 0) or 0
                        ),
                        "offensive_rebounds": game_row.get(
                            "away_team_offensive_rebounds", 0
                        ),
                        "defensive_rebounds": game_row.get(
                            "away_team_defensive_rebounds", 0
                        ),
                        "total_rebounds": game_row.get("away_team_total_rebounds", 0),
                        "assists": game_row.get("away_team_assists", 0),
                        "steals": game_row.get("away_team_steals", 0),
                        "blocks": game_row.get("away_team_blocks", 0),
                        "turnovers": game_row.get("away_team_turnovers", 0),
                        "fouls": game_row.get("away_team_fouls", 0),
                    },
                },
            },
            "game_info": {
                "game_id": str(game_row["game_id"]),
                "season_year": season_year,
                "season": f"{season_year}-{str(season_year + 1)[-2:]}",
                "game_date": game_date.isoformat(),
                "season_type": season_type,
                "season_type_label": {
                    1: "Preseason",
                    2: "Regular Season",
                    3: "Playoffs",
                    5: "Play-In Tournament",
                }.get(season_type, "Unknown"),
                "attendance": game_row.get("attendance"),
            },
            "espn_features": {
                "box_score": {
                    "home": {"players": home_players},
                    "away": {"players": away_players},
                }
            },
            "play_by_play": {
                "total_plays": play_count,
                "summary": {"has_data": play_count > 0},
            },
            "source_data": {
                "source": "ESPN",
                "original_game_id": str(game_row["game_id"]),
                "loaded_from": "espn_database",
                "loaded_at": datetime.now().isoformat(),
            },
            "metadata": {
                "enrichment": {
                    "enriched_at": datetime.now().isoformat(),
                    "format_version": 2,
                    "migration_source": "espn_db",
                }
            },
        }

        return enriched_data

    def migrate_games(self, batch_size: int = 1000, limit: Optional[int] = None):
        """
        Migrate games from espn.nba.nba_box_score_teams to espn.espn_games.

        Also creates corresponding records in espn.espn_team_stats.

        Args:
            batch_size: Number of games to process per batch
            limit: Optional limit on number of games to process (for testing)
        """
        logger.info("=" * 70)
        logger.info("MIGRATING GAMES")
        logger.info("=" * 70)

        if self.dry_run:
            logger.info("[DRY RUN] Preview mode - no data will be inserted")

        # Query all games from source
        query = """
        SELECT
            t.game_id,
            t.game_date,
            t.home_team_id,
            t.home_team_abbrev,
            t.home_team_score,
            t.away_team_id,
            t.away_team_abbrev,
            t.away_team_score,
            t.attendance,
            t.game_state,
            -- Home team stats
            t.home_team_field_goals,
            t.home_team_field_goals_pct,
            t.home_team_three_pointers,
            t.home_team_three_pointers_pct,
            t.home_team_free_throws,
            t.home_team_free_throws_pct,
            t.home_team_offensive_rebounds,
            t.home_team_defensive_rebounds,
            t.home_team_total_rebounds,
            t.home_team_assists,
            t.home_team_steals,
            t.home_team_blocks,
            t.home_team_turnovers,
            t.home_team_fouls,
            -- Away team stats
            t.away_team_field_goals,
            t.away_team_field_goals_pct,
            t.away_team_three_pointers,
            t.away_team_three_pointers_pct,
            t.away_team_free_throws,
            t.away_team_free_throws_pct,
            t.away_team_offensive_rebounds,
            t.away_team_defensive_rebounds,
            t.away_team_total_rebounds,
            t.away_team_assists,
            t.away_team_steals,
            t.away_team_blocks,
            t.away_team_turnovers,
            t.away_team_fouls
        FROM nba.nba_box_score_teams t
        ORDER BY t.game_date
        """

        # Add LIMIT clause if specified
        if limit:
            query += f" LIMIT {limit}"

        with self.source_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            total_games = cursor.rowcount
            logger.info(f"Found {total_games:,} games in source database")

            games_processed = 0
            start_time = datetime.now()

            while True:
                games_batch = cursor.fetchmany(batch_size)
                if not games_batch:
                    break

                for game_row in games_batch:
                    games_processed += 1
                    game_id = str(game_row["game_id"])

                    try:
                        # Get player stats for this game
                        player_rows = self._get_player_stats(game_id)

                        # Get play count
                        play_count = self._get_play_count(game_id)

                        # Get season_type (JSON or date inference)
                        season_type, source = self.get_season_type(
                            game_id, game_row["game_date"]
                        )

                        if not season_type:
                            logger.warning(
                                f"[{games_processed}/{total_games}] Game {game_id}: Failed to get season_type"
                            )
                            self.stats["games_failed"] += 1
                            self.stats["season_type_failed"] += 1
                            continue

                        if source == "json":
                            self.stats["season_type_from_json"] += 1
                        elif source == "date_inference":
                            self.stats["season_type_from_date"] += 1

                        # Build full JSONB structure
                        jsonb_data = self.build_game_jsonb(
                            game_row, player_rows, play_count, season_type
                        )

                        # Insert/update in target database
                        if not self.dry_run:
                            self._upsert_game(
                                game_id, game_row, season_type, jsonb_data
                            )
                            self._insert_team_stats(game_id, game_row, season_type)

                        self.stats["games_migrated"] += 1

                        # Progress logging
                        if games_processed % 100 == 0:
                            elapsed = (datetime.now() - start_time).total_seconds()
                            rate = games_processed / elapsed if elapsed > 0 else 0
                            logger.info(
                                f"[{games_processed:,}/{total_games:,}] "
                                f"Processed {games_processed:,} games "
                                f"({rate:.1f} games/sec)"
                            )

                    except Exception as e:
                        logger.error(
                            f"Error processing game {game_id}: {e}", exc_info=True
                        )
                        self.stats["games_failed"] += 1

        # Final summary
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("")
        logger.info("=" * 70)
        logger.info("GAMES MIGRATION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total time: {elapsed/60:.1f} minutes")
        logger.info(f"Games migrated: {self.stats['games_migrated']:,}")
        logger.info(f"Games failed: {self.stats['games_failed']:,}")
        logger.info(f"seasonType from JSON: {self.stats['season_type_from_json']:,}")
        logger.info(f"seasonType from dates: {self.stats['season_type_from_date']:,}")
        logger.info(f"seasonType failed: {self.stats['season_type_failed']:,}")
        logger.info(f"Team stats inserted: {self.stats['team_stats_inserted']:,}")
        logger.info("=" * 70)

    def _get_player_stats(self, game_id: str) -> List[Dict]:
        """Get player box scores for a game."""
        query = """
        SELECT *
        FROM nba.nba_box_score_players
        WHERE game_id = %s
        ORDER BY team_abbrev, player_id
        """

        with self.source_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (int(game_id),))
            return cursor.fetchall()

    def _get_play_count(self, game_id: str) -> int:
        """Get play count for a game."""
        query = "SELECT COUNT(*) as count FROM nba.plays WHERE game_id = %s"

        with self.source_conn.cursor() as cursor:
            cursor.execute(query, (int(game_id),))
            result = cursor.fetchone()
            return result[0] if result else 0

    def _upsert_game(
        self, game_id: str, game_row: Dict, season_type: int, jsonb_data: Dict
    ):
        """Insert or update game in target database."""
        # Calculate season year
        game_date = game_row["game_date"]
        season_year = game_date.year if game_date.month >= 10 else game_date.year - 1

        query = """
        INSERT INTO espn.espn_games (
            game_id, season, season_type, game_date,
            home_team, away_team, home_score, away_score,
            collected_at, updated_at, data, metadata
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        ON CONFLICT (game_id) DO UPDATE SET
            season_type = EXCLUDED.season_type,
            home_team = EXCLUDED.home_team,
            away_team = EXCLUDED.away_team,
            home_score = EXCLUDED.home_score,
            away_score = EXCLUDED.away_score,
            updated_at = EXCLUDED.updated_at,
            data = EXCLUDED.data,
            metadata = EXCLUDED.metadata
        """

        with self.target_conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    game_id,
                    season_year,
                    season_type,
                    game_date,
                    game_row["home_team_abbrev"],
                    game_row["away_team_abbrev"],
                    game_row.get("home_team_score"),
                    game_row.get("away_team_score"),
                    datetime.now(),
                    datetime.now(),
                    Json(jsonb_data),
                    Json(jsonb_data.get("metadata", {})),
                ),
            )
            self.target_conn.commit()

    def _insert_team_stats(self, game_id: str, game_row: Dict, season_type: int):
        """Insert team stats for both teams."""
        # Calculate season year
        game_date = game_row["game_date"]
        season_year = game_date.year if game_date.month >= 10 else game_date.year - 1

        # Create 2 rows: home and away
        team_stats = [
            {
                "game_id": game_id,
                "team_id": str(game_row["home_team_id"]),
                "team_name": game_row["home_team_abbrev"],
                "is_home": True,
                "season": season_year,
                "season_type": season_type,
                "game_date": game_date,
                "points": game_row.get("home_team_score"),
                "data": {
                    "stats": {
                        "field_goals": game_row.get("home_team_field_goals"),
                        "field_goals_pct": float(
                            game_row.get("home_team_field_goals_pct", 0) or 0
                        ),
                        "three_pointers": game_row.get("home_team_three_pointers"),
                        "three_pointers_pct": float(
                            game_row.get("home_team_three_pointers_pct", 0) or 0
                        ),
                        "free_throws": game_row.get("home_team_free_throws"),
                        "free_throws_pct": float(
                            game_row.get("home_team_free_throws_pct", 0) or 0
                        ),
                        "rebounds": game_row.get("home_team_total_rebounds", 0),
                        "assists": game_row.get("home_team_assists", 0),
                        "steals": game_row.get("home_team_steals", 0),
                        "blocks": game_row.get("home_team_blocks", 0),
                        "turnovers": game_row.get("home_team_turnovers", 0),
                        "fouls": game_row.get("home_team_fouls", 0),
                    }
                },
            },
            {
                "game_id": game_id,
                "team_id": str(game_row["away_team_id"]),
                "team_name": game_row["away_team_abbrev"],
                "is_home": False,
                "season": season_year,
                "season_type": season_type,
                "game_date": game_date,
                "points": game_row.get("away_team_score"),
                "data": {
                    "stats": {
                        "field_goals": game_row.get("away_team_field_goals"),
                        "field_goals_pct": float(
                            game_row.get("away_team_field_goals_pct", 0) or 0
                        ),
                        "three_pointers": game_row.get("away_team_three_pointers"),
                        "three_pointers_pct": float(
                            game_row.get("away_team_three_pointers_pct", 0) or 0
                        ),
                        "free_throws": game_row.get("away_team_free_throws"),
                        "free_throws_pct": float(
                            game_row.get("away_team_free_throws_pct", 0) or 0
                        ),
                        "rebounds": game_row.get("away_team_total_rebounds", 0),
                        "assists": game_row.get("away_team_assists", 0),
                        "steals": game_row.get("away_team_steals", 0),
                        "blocks": game_row.get("away_team_blocks", 0),
                        "turnovers": game_row.get("away_team_turnovers", 0),
                        "fouls": game_row.get("away_team_fouls", 0),
                    }
                },
            },
        ]

        query = """
        INSERT INTO espn.espn_team_stats (
            game_id, team_id, team_name, is_home, season, season_type,
            game_date, points, collected_at, updated_at, data, metadata
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (game_id, team_id) DO UPDATE SET
            team_name = EXCLUDED.team_name,
            season_type = EXCLUDED.season_type,
            points = EXCLUDED.points,
            updated_at = EXCLUDED.updated_at,
            data = EXCLUDED.data
        """

        with self.target_conn.cursor() as cursor:
            for ts in team_stats:
                cursor.execute(
                    query,
                    (
                        ts["game_id"],
                        ts["team_id"],
                        ts["team_name"],
                        ts["is_home"],
                        ts["season"],
                        ts["season_type"],
                        ts["game_date"],
                        ts["points"],
                        datetime.now(),
                        datetime.now(),
                        Json(ts["data"]),
                        Json({"migration_source": "espn_db"}),
                    ),
                )
                self.stats["team_stats_inserted"] += 1

            self.target_conn.commit()

    def migrate_plays(self, batch_size: int = 10000):
        """
        Migrate plays from espn.nba.plays to espn.espn_plays.

        Args:
            batch_size: Number of plays to process per batch
        """
        logger.info("=" * 70)
        logger.info("MIGRATING PLAYS")
        logger.info("=" * 70)

        if self.dry_run:
            logger.info("[DRY RUN] Preview mode - no data will be inserted")
            return

        # Direct SQL migration with batch inserts
        query_source = """
        SELECT
            game_id, play_id, period, period_name, game_clock,
            description, home_score, away_score, team_type
        FROM nba.plays
        ORDER BY game_id, id
        """

        query_insert = """
        INSERT INTO espn.espn_plays (
            game_id, play_id, period, clock, description,
            home_score, away_score, collected_at, data, metadata
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
        ON CONFLICT DO NOTHING
        """

        with self.source_conn.cursor(cursor_factory=RealDictCursor) as src_cursor:
            src_cursor.execute(query_source)
            total_plays = src_cursor.rowcount
            logger.info(f"Found {total_plays:,} plays in source database")

            start_time = datetime.now()
            plays_processed = 0

            with self.target_conn.cursor() as tgt_cursor:
                while True:
                    plays_batch = src_cursor.fetchmany(batch_size)
                    if not plays_batch:
                        break

                    # Prepare batch insert data
                    batch_data = []
                    for play in plays_batch:
                        jsonb_data = {
                            "play_id": str(play["play_id"]),
                            "period": play["period"],
                            "period_name": play.get("period_name"),
                            "clock": play.get("game_clock"),
                            "description": play.get("description"),
                            "team_type": play.get("team_type"),
                        }

                        batch_data.append(
                            (
                                str(play["game_id"]),
                                str(play["play_id"]),
                                play["period"],
                                play.get("game_clock"),
                                play.get("description"),
                                play.get("home_score"),
                                play.get("away_score"),
                                datetime.now(),
                                Json(jsonb_data),
                                Json({"migration_source": "espn_db"}),
                            )
                        )

                    # Batch insert
                    execute_batch(
                        tgt_cursor, query_insert, batch_data, page_size=batch_size
                    )
                    self.target_conn.commit()

                    plays_processed += len(batch_data)
                    self.stats["plays_migrated"] = plays_processed

                    # Progress logging
                    if plays_processed % 100000 == 0:
                        elapsed = (datetime.now() - start_time).total_seconds()
                        rate = plays_processed / elapsed if elapsed > 0 else 0
                        logger.info(
                            f"[{plays_processed:,}/{total_plays:,}] "
                            f"Processed {plays_processed:,} plays "
                            f"({rate:.0f} plays/sec)"
                        )

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("")
        logger.info("=" * 70)
        logger.info("PLAYS MIGRATION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total time: {elapsed/60:.1f} minutes")
        logger.info(f"Plays migrated: {self.stats['plays_migrated']:,}")
        logger.info("=" * 70)

    def migrate_schedules(self):
        """
        Migrate schedules from espn.nba.nba_box_score_teams to espn.espn_schedules.

        Groups games by date and aggregates into JSONB.
        """
        logger.info("=" * 70)
        logger.info("MIGRATING SCHEDULES")
        logger.info("=" * 70)

        if self.dry_run:
            logger.info("[DRY RUN] Preview mode - no data will be inserted")
            return

        query = """
        INSERT INTO espn.espn_schedules (
            schedule_date, season, num_games, collected_at, updated_at, data, metadata
        )
        SELECT
            game_date::date as schedule_date,
            EXTRACT(YEAR FROM game_date)::INTEGER -
                CASE WHEN EXTRACT(MONTH FROM game_date) < 10 THEN 1 ELSE 0 END as season,
            COUNT(*) as num_games,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            jsonb_agg(
                jsonb_build_object(
                    'game_id', CAST(game_id AS VARCHAR),
                    'home_team', home_team_abbrev,
                    'away_team', away_team_abbrev,
                    'time', game_date,
                    'status', game_state,
                    'home_score', home_team_score,
                    'away_score', away_team_score
                )
            ) as data,
            '{"migration_source": "espn_db"}'::jsonb as metadata
        FROM espn.nba.nba_box_score_teams
        GROUP BY game_date::date
        ON CONFLICT (schedule_date) DO UPDATE SET
            num_games = EXCLUDED.num_games,
            updated_at = EXCLUDED.updated_at,
            data = EXCLUDED.data
        """

        start_time = datetime.now()

        try:
            with self.target_conn.cursor() as cursor:
                # Use dblink to query source database
                cursor.execute(query)
                self.target_conn.commit()
                self.stats["schedules_migrated"] = cursor.rowcount
        except Exception as e:
            logger.error(f"Direct migration failed, falling back to Python method: {e}")
            # Rollback the failed transaction before retrying
            self.target_conn.rollback()
            # Fallback: query source, aggregate in Python, insert to target
            self._migrate_schedules_fallback()

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("")
        logger.info("=" * 70)
        logger.info("SCHEDULES MIGRATION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total time: {elapsed:.1f} seconds")
        logger.info(f"Schedules migrated: {self.stats['schedules_migrated']:,}")
        logger.info("=" * 70)

    def _migrate_schedules_fallback(self):
        """Fallback method for schedule migration using Python aggregation."""
        # Query all games from source
        query_source = """
        SELECT
            game_id, game_date, home_team_abbrev, away_team_abbrev,
            game_state, home_team_score, away_team_score
        FROM nba.nba_box_score_teams
        ORDER BY game_date
        """

        with self.source_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query_source)
            games = cursor.fetchall()

        # Group by date
        from collections import defaultdict

        schedules = defaultdict(list)

        for game in games:
            date = game["game_date"].date()
            schedules[date].append(
                {
                    "game_id": str(game["game_id"]),
                    "home_team": game["home_team_abbrev"],
                    "away_team": game["away_team_abbrev"],
                    "time": game["game_date"].isoformat(),
                    "status": game.get("game_state"),
                    "home_score": game.get("home_team_score"),
                    "away_score": game.get("away_team_score"),
                }
            )

        # Insert into target
        query_insert = """
        INSERT INTO espn.espn_schedules (
            schedule_date, season, num_games, collected_at, updated_at, data, metadata
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (schedule_date) DO UPDATE SET
            num_games = EXCLUDED.num_games,
            updated_at = EXCLUDED.updated_at,
            data = EXCLUDED.data
        """

        with self.target_conn.cursor() as cursor:
            for date, games_list in schedules.items():
                season_year = date.year if date.month >= 10 else date.year - 1

                cursor.execute(
                    query_insert,
                    (
                        date,
                        season_year,
                        len(games_list),
                        datetime.now(),
                        datetime.now(),
                        Json(games_list),
                        Json({"migration_source": "espn_db"}),
                    ),
                )

            self.target_conn.commit()
            self.stats["schedules_migrated"] = len(schedules)

    def print_summary(self):
        """Print final migration summary."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Games migrated:        {self.stats['games_migrated']:,}")
        logger.info(f"Team stats inserted:   {self.stats['team_stats_inserted']:,}")
        logger.info(f"Plays migrated:        {self.stats['plays_migrated']:,}")
        logger.info(f"Schedules migrated:    {self.stats['schedules_migrated']:,}")
        logger.info("")
        logger.info(f"seasonType from JSON:  {self.stats['season_type_from_json']:,}")
        logger.info(f"seasonType from dates: {self.stats['season_type_from_date']:,}")
        logger.info(f"seasonType failed:     {self.stats['season_type_failed']:,}")
        logger.info("")
        logger.info(f"Games failed:          {self.stats['games_failed']:,}")
        logger.info("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate ESPN database to nba_simulator.espn schema"
    )
    parser.add_argument("--source-db", default="espn", help="Source database name")
    parser.add_argument(
        "--target-db", default="nba_simulator", help="Target database name"
    )
    parser.add_argument(
        "--json-path",
        default="/Users/ryanranft/0espn/data/nba/nba_box_score",
        help="Path to ESPN JSON files",
    )
    parser.add_argument(
        "--batch-size", type=int, default=1000, help="Batch size for processing"
    )
    parser.add_argument(
        "--limit", type=int, help="Limit number of games to process (for testing)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without inserting"
    )
    parser.add_argument(
        "--skip-games", action="store_true", help="Skip games migration"
    )
    parser.add_argument(
        "--skip-plays", action="store_true", help="Skip plays migration"
    )
    parser.add_argument(
        "--skip-schedules", action="store_true", help="Skip schedules migration"
    )
    parser.add_argument(
        "--skip-team-stats", action="store_true", help="Skip team stats migration"
    )

    args = parser.parse_args()

    # Initialize migrator
    migrator = ESPNDatabaseMigrator(
        source_db=args.source_db,
        target_db=args.target_db,
        json_path=args.json_path,
        dry_run=args.dry_run,
    )

    try:
        # Connect to databases
        migrator.connect()

        # Run migrations
        if not args.skip_games:
            migrator.migrate_games(batch_size=args.batch_size, limit=args.limit)

        if not args.skip_plays:
            migrator.migrate_plays(batch_size=10000)

        if not args.skip_schedules:
            migrator.migrate_schedules()

        # Print summary
        migrator.print_summary()

        logger.info("")
        logger.info("✅ MIGRATION COMPLETE!")

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return 1

    finally:
        migrator.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
