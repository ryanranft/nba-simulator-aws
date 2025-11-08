#!/usr/bin/env python3
"""
ESPN Feature Enrichment ETL Pipeline

Enriches raw_data.nba_games with complete 58-feature set from ESPN JSON files in S3.

Features:
- Batch processing with configurable batch size
- Checkpoint/resume capability
- Dry-run mode for testing
- Progress monitoring and statistics
- Error handling and logging

Usage:
    # Dry-run on 100 games
    python scripts/enrichment/espn_enrichment_etl.py --dry-run --limit 100

    # Test on 1,000 games
    python scripts/enrichment/espn_enrichment_etl.py --limit 1000

    # Full backfill with checkpointing
    python scripts/enrichment/espn_enrichment_etl.py --checkpoint enrichment_progress.json

    # Resume from checkpoint
    python scripts/enrichment/espn_enrichment_etl.py --resume enrichment_progress.json
"""

import sys
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nba_simulator.etl.extractors.espn import ESPNFeatureExtractor
from nba_simulator.config import config


class EnrichmentETL:
    """ESPN feature enrichment ETL pipeline"""

    def __init__(
        self,
        batch_size: int = 100,
        dry_run: bool = False,
        checkpoint_file: Optional[str] = None,
        verbose: bool = False,
        db_config: Optional[Dict] = None,
    ):
        """
        Initialize enrichment ETL.

        Args:
            batch_size: Number of games to process per batch
            dry_run: If True, don't write to database
            checkpoint_file: Path to checkpoint file for resume capability
            verbose: Enable verbose logging
            db_config: Optional database configuration override
        """
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.checkpoint_file = checkpoint_file
        self.verbose = verbose
        self.db_config_override = db_config or {}

        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

        # Initialize extractor
        self.extractor = ESPNFeatureExtractor()

        # Statistics
        self.stats = {
            "total_games": 0,
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "format_1_count": 0,
            "format_2_count": 0,
            "errors": defaultdict(int),
            "start_time": None,
            "end_time": None,
        }

        # Checkpoint data
        self.checkpoint = {
            "last_game_id": None,
            "processed_count": 0,
            "batch_number": 0,
            "timestamp": None,
        }

        # Database connection
        self.conn = None
        self.cursor = None

    def connect_database(self):
        """Connect to PostgreSQL database"""
        import os

        # Priority: override config > environment variables > defaults
        conn_params = {
            "host": self.db_config_override.get("host")
            or os.getenv("POSTGRES_HOST", "localhost"),
            "port": self.db_config_override.get("port")
            or int(os.getenv("POSTGRES_PORT", "5432")),
            "database": self.db_config_override.get("database")
            or os.getenv("POSTGRES_DB", "nba_simulator"),
            "user": self.db_config_override.get("user")
            or os.getenv("POSTGRES_USER", "ryanranft"),
            "password": self.db_config_override.get("password", "")
            or os.getenv("POSTGRES_PASSWORD", ""),
        }

        self.conn = psycopg2.connect(**conn_params)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        self.logger.info(
            f"Connected to database: {conn_params['database']}@{conn_params['host']}"
        )

    def load_checkpoint(self, checkpoint_file: str) -> bool:
        """
        Load checkpoint from file.

        Returns:
            True if checkpoint loaded successfully
        """
        checkpoint_path = Path(checkpoint_file)
        if not checkpoint_path.exists():
            self.logger.warning(f"Checkpoint file not found: {checkpoint_file}")
            return False

        try:
            with open(checkpoint_path, "r") as f:
                self.checkpoint = json.load(f)
            self.logger.info(
                f"Loaded checkpoint: {self.checkpoint['processed_count']} games processed"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            return False

    def save_checkpoint(self):
        """Save checkpoint to file"""
        if not self.checkpoint_file:
            return

        self.checkpoint["timestamp"] = datetime.now().isoformat()

        try:
            checkpoint_path = Path(self.checkpoint_file)
            with open(checkpoint_path, "w") as f:
                json.dump(self.checkpoint, f, indent=2)
            self.logger.debug(
                f"Saved checkpoint: {self.checkpoint['processed_count']} games"
            )
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")

    def get_games_to_process(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get list of games to process from database.

        Args:
            limit: Maximum number of games to process

        Returns:
            List of game records
        """
        # Build query
        query = """
            SELECT game_id, data
            FROM raw_data.nba_games
            WHERE 1=1
        """

        params = []

        # Resume from checkpoint if available
        if self.checkpoint.get("last_game_id"):
            query += " AND game_id > %s"
            params.append(self.checkpoint["last_game_id"])

        query += " ORDER BY game_id"

        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query, params)
        games = self.cursor.fetchall()

        self.logger.info(f"Found {len(games)} games to process")
        return games

    def merge_features_into_jsonb(
        self, existing_data: Dict, extracted_features: Dict
    ) -> Dict:
        """
        Merge extracted features into existing JSONB data.

        Strategy:
        - Preserve existing game data
        - Add new 'espn_features' section with all extracted features
        - Add enrichment metadata

        Args:
            existing_data: Existing data from database
            extracted_features: Newly extracted features

        Returns:
            Merged JSONB data
        """
        # Create a copy of existing data
        merged = existing_data.copy() if existing_data else {}

        # Add extracted features under 'espn_features' key
        merged["espn_features"] = extracted_features

        # Add enrichment metadata
        if "metadata" not in merged:
            merged["metadata"] = {}

        merged["metadata"]["enrichment"] = {
            "enriched_at": datetime.now().isoformat(),
            "format_version": extracted_features.get("source_data", {}).get("format"),
            "feature_count": self._count_features(extracted_features),
        }

        return merged

    def _count_features(self, features: Dict) -> int:
        """Count number of features in extracted data"""
        count = 0

        # Game info features
        if features.get("game_info"):
            count += len(features["game_info"])

        # Scoring features
        if features.get("scoring"):
            count += 2  # home and away totals

        # Venue features
        if features.get("venue"):
            count += 3  # name, city, state

        # Officials
        if features.get("officials"):
            count += 1

        # Box score features (per player)
        box_score = features.get("box_score", {})
        for team in ["home", "away"]:
            players = box_score.get(team, {}).get("players", [])
            for player in players:
                if player.get("stats"):
                    count += len(player["stats"])

        # Play-by-play features
        if features.get("plays_summary"):
            count += 3  # total_plays, periods, event_types

        return count

    def process_batch(self, games: List[Dict]) -> Dict[str, int]:
        """
        Process a batch of games.

        Args:
            games: List of game records

        Returns:
            Batch statistics
        """
        batch_stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "format_1": 0,
            "format_2": 0,
        }

        updates = []  # List of (game_id, merged_data) tuples

        for game in games:
            game_id = game["game_id"]
            existing_data = game["data"]

            try:
                # Extract features from S3
                extracted_features = self.extractor.extract_game_features(
                    game_id=game_id
                )

                if extracted_features is None:
                    self.logger.warning(
                        f"Failed to extract features for game {game_id}"
                    )
                    batch_stats["failed"] += 1
                    self.stats["errors"]["extraction_failed"] += 1
                    continue

                # Track format
                format_version = extracted_features.get("source_data", {}).get("format")
                if format_version == 1:
                    batch_stats["format_1"] += 1
                    self.stats["format_1_count"] += 1
                elif format_version == 2:
                    batch_stats["format_2"] += 1
                    self.stats["format_2_count"] += 1

                # Merge features
                merged_data = self.merge_features_into_jsonb(
                    existing_data, extracted_features
                )

                # Add to update list
                updates.append((game_id, json.dumps(merged_data)))

                batch_stats["successful"] += 1
                batch_stats["processed"] += 1

                if self.verbose:
                    self.logger.debug(f"✓ {game_id} (Format {format_version})")

            except Exception as e:
                self.logger.error(f"Error processing game {game_id}: {e}")
                batch_stats["failed"] += 1
                batch_stats["processed"] += 1
                self.stats["errors"][str(type(e).__name__)] += 1

        # Write updates to database (if not dry-run)
        if not self.dry_run and updates:
            self._write_batch_to_database(updates)
        elif self.dry_run:
            self.logger.info(f"DRY-RUN: Would update {len(updates)} games")

        return batch_stats

    def _write_batch_to_database(self, updates: List[tuple]):
        """
        Write batch updates to database.

        Args:
            updates: List of (game_id, merged_data_json) tuples
        """
        try:
            # Use execute_values for efficient batch update
            execute_values(
                self.cursor,
                """
                UPDATE raw_data.nba_games
                SET data = data_update.merged_data::jsonb,
                    updated_at = NOW()
                FROM (VALUES %s) AS data_update(game_id, merged_data)
                WHERE nba_games.game_id = data_update.game_id
                """,
                updates,
                template="(%s, %s)",
            )

            self.conn.commit()
            self.logger.debug(f"Committed {len(updates)} updates to database")

        except Exception as e:
            self.logger.error(f"Failed to write batch to database: {e}")
            self.conn.rollback()
            raise

    def run(self, limit: Optional[int] = None, resume: bool = False):
        """
        Run the enrichment ETL pipeline.

        Args:
            limit: Maximum number of games to process
            resume: Resume from checkpoint
        """
        self.stats["start_time"] = datetime.now()

        try:
            # Connect to database
            self.connect_database()

            # Load checkpoint if resuming
            if resume and self.checkpoint_file:
                self.load_checkpoint(self.checkpoint_file)

            # Get games to process
            games = self.get_games_to_process(limit)
            self.stats["total_games"] = len(games)

            if not games:
                self.logger.info("No games to process")
                return

            # Process in batches
            total_batches = (len(games) + self.batch_size - 1) // self.batch_size

            self.logger.info(
                f"Processing {len(games)} games in {total_batches} batches"
            )
            self.logger.info(f"Batch size: {self.batch_size}")
            self.logger.info(f"Dry-run: {self.dry_run}")

            for batch_num in range(total_batches):
                batch_start = batch_num * self.batch_size
                batch_end = min(batch_start + self.batch_size, len(games))
                batch = games[batch_start:batch_end]

                self.logger.info(
                    f"Processing batch {batch_num + 1}/{total_batches} ({len(batch)} games)"
                )

                batch_start_time = time.time()
                batch_stats = self.process_batch(batch)
                batch_elapsed = time.time() - batch_start_time

                # Update overall stats
                self.stats["processed"] += batch_stats["processed"]
                self.stats["successful"] += batch_stats["successful"]
                self.stats["failed"] += batch_stats["failed"]

                # Update checkpoint
                self.checkpoint["last_game_id"] = batch[-1]["game_id"]
                self.checkpoint["processed_count"] = self.stats["processed"]
                self.checkpoint["batch_number"] = batch_num + 1
                self.save_checkpoint()

                # Log batch results
                success_rate = (
                    (batch_stats["successful"] / batch_stats["processed"] * 100)
                    if batch_stats["processed"] > 0
                    else 0
                )
                games_per_sec = (
                    batch_stats["processed"] / batch_elapsed if batch_elapsed > 0 else 0
                )

                self.logger.info(
                    f"Batch {batch_num + 1} complete: "
                    f"{batch_stats['successful']}/{batch_stats['processed']} successful "
                    f"({success_rate:.1f}%) | "
                    f"Format 1: {batch_stats['format_1']}, Format 2: {batch_stats['format_2']} | "
                    f"{games_per_sec:.1f} games/sec"
                )

            self.stats["end_time"] = datetime.now()
            self._print_summary()

        except KeyboardInterrupt:
            self.logger.warning("Interrupted by user")
            self.save_checkpoint()
            raise

        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            self.save_checkpoint()
            raise

        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()

    def _print_summary(self):
        """Print enrichment summary"""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        success_rate = (
            (self.stats["successful"] / self.stats["processed"] * 100)
            if self.stats["processed"] > 0
            else 0
        )

        print("\n" + "=" * 60)
        print("ENRICHMENT ETL SUMMARY")
        print("=" * 60)
        print(f"Total games: {self.stats['total_games']}")
        print(f"Processed: {self.stats['processed']}")
        print(f"Successful: {self.stats['successful']} ({success_rate:.1f}%)")
        print(f"Failed: {self.stats['failed']}")
        print(f"Format 1 (old): {self.stats['format_1_count']}")
        print(f"Format 2 (new): {self.stats['format_2_count']}")
        print(f"\nDuration: {duration:.1f} seconds")
        print(f"Rate: {self.stats['processed'] / duration:.1f} games/sec")

        if self.stats["errors"]:
            print(f"\nErrors by type:")
            for error_type, count in self.stats["errors"].items():
                print(f"  {error_type}: {count}")

        if self.dry_run:
            print(f"\n⚠️  DRY-RUN MODE - No changes written to database")
        else:
            print(f"\n✅ Enrichment complete!")

        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="ESPN Feature Enrichment ETL Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Database connection arguments
    parser.add_argument("--host", type=str, help="Database host (default: localhost)")
    parser.add_argument("--port", type=int, help="Database port (default: 5432)")
    parser.add_argument(
        "--database", type=str, help="Database name (default: nba_simulator)"
    )
    parser.add_argument("--user", type=str, help="Database user (default: ryanranft)")
    parser.add_argument("--password", type=str, help='Database password (default: "")')

    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of games to process per batch (default: 100)",
    )

    parser.add_argument(
        "--limit", type=int, help="Maximum number of games to process (for testing)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing to database (for testing)",
    )

    parser.add_argument(
        "--checkpoint", type=str, help="Path to checkpoint file for resume capability"
    )

    parser.add_argument(
        "--resume", action="store_true", help="Resume from checkpoint file"
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Validate arguments
    if args.resume and not args.checkpoint:
        parser.error("--resume requires --checkpoint to be specified")

    # Build database config from arguments
    db_config = {}
    if args.host:
        db_config["host"] = args.host
    if args.port:
        db_config["port"] = args.port
    if args.database:
        db_config["database"] = args.database
    if args.user:
        db_config["user"] = args.user
    if args.password is not None:
        db_config["password"] = args.password

    # Create ETL instance
    etl = EnrichmentETL(
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        checkpoint_file=args.checkpoint,
        verbose=args.verbose,
        db_config=db_config,
    )

    # Run enrichment
    etl.run(limit=args.limit, resume=args.resume)


if __name__ == "__main__":
    main()
