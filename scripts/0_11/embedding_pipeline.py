#!/usr/bin/env python3
"""
Phase 0.11: Embedding Pipeline for RAG

Purpose: Generate and store vector embeddings for NBA data
Created: October 25, 2025
Implementation ID: rec_034_pgvector

Usage:
    python scripts/0_11/embedding_pipeline.py --entity-type player --limit 100
    python scripts/0_11/embedding_pipeline.py --entity-type game --batch-size 50
    python scripts/0_11/embedding_pipeline.py --all
"""

import os
import sys
import argparse
import json
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import psycopg2
from psycopg2.extras import Json
import boto3
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.0_11.openai_embedder import OpenAIEmbedder
from scripts.0_11.batch_processor import BatchProcessor


class EmbeddingPipeline:
    """
    Main pipeline for generating and storing NBA data embeddings

    Processes data from:
    - raw_data.nba_games (JSONB game data)
    - raw_data.nba_players (JSONB player data)
    - S3 raw data files

    Stores embeddings in:
    - rag.nba_embeddings
    - rag.play_embeddings
    """

    def __init__(self, batch_size: int = 100, dry_run: bool = False):
        """
        Initialize embedding pipeline

        Args:
            batch_size: Number of records to process per batch
            dry_run: If True, don't actually insert embeddings
        """
        self.batch_size = batch_size
        self.dry_run = dry_run

        # Initialize components
        self.embedder = OpenAIEmbedder()
        self.batch_processor = BatchProcessor(batch_size=batch_size)

        # Database connection
        self.conn = self._create_db_connection()
        self.cursor = self.conn.cursor()

        # S3 client
        self.s3_client = boto3.client('s3')
        self.bucket_name = 'nba-sim-raw-data-lake'

        # Statistics
        self.stats = {
            'total_processed': 0,
            'total_embedded': 0,
            'total_failed': 0,
            'total_cost_usd': 0.0,
            'total_tokens': 0
        }

    def _create_db_connection(self):
        """Create PostgreSQL database connection"""
        config = {
            'host': os.getenv('RDS_HOST', os.getenv('POSTGRES_HOST', 'localhost')),
            'port': int(os.getenv('RDS_PORT', os.getenv('POSTGRES_PORT', '5432'))),
            'database': os.getenv('RDS_DATABASE', os.getenv('POSTGRES_DB', 'nba_data')),
            'user': os.getenv('RDS_USER', os.getenv('POSTGRES_USER', 'postgres')),
            'password': os.getenv('RDS_PASSWORD', os.getenv('POSTGRES_PASSWORD', ''))
        }

        return psycopg2.connect(**config)

    def generate_player_text(self, player_data: Dict) -> str:
        """
        Generate descriptive text for player embedding

        Args:
            player_data: Player data from JSONB or dict

        Returns:
            Formatted text string for embedding
        """
        # Extract player info
        name = player_data.get('player_name', player_data.get('displayName', 'Unknown'))
        position = player_data.get('position', player_data.get('pos', ''))
        team = player_data.get('team', player_data.get('team_abbr', ''))

        # Build descriptive text
        text_parts = [f"Player: {name}"]

        if position:
            text_parts.append(f"Position: {position}")
        if team:
            text_parts.append(f"Team: {team}")

        # Add career stats if available
        stats = player_data.get('career_stats', player_data.get('stats', {}))
        if stats:
            if 'points' in stats:
                text_parts.append(f"Career Points: {stats['points']}")
            if 'assists' in stats:
                text_parts.append(f"Career Assists: {stats['assists']}")
            if 'rebounds' in stats:
                text_parts.append(f"Career Rebounds: {stats['rebounds']}")
            if 'games_played' in stats:
                text_parts.append(f"Games Played: {stats['games_played']}")

        # Add bio info
        if 'height' in player_data:
            text_parts.append(f"Height: {player_data['height']}")
        if 'weight' in player_data:
            text_parts.append(f"Weight: {player_data['weight']}")
        if 'college' in player_data:
            text_parts.append(f"College: {player_data['college']}")
        if 'draft_year' in player_data:
            text_parts.append(f"Draft Year: {player_data['draft_year']}")

        return ". ".join(text_parts) + "."

    def generate_game_text(self, game_data: Dict) -> str:
        """
        Generate descriptive text for game embedding

        Args:
            game_data: Game data from JSONB or dict

        Returns:
            Formatted text string for embedding
        """
        # Extract game info
        game_id = game_data.get('game_id', game_data.get('id', 'Unknown'))
        date = game_data.get('game_date', game_data.get('date', ''))
        season = game_data.get('season', '')

        home_team = game_data.get('home_team', game_data.get('homeTeam', {}).get('abbreviation', ''))
        away_team = game_data.get('away_team', game_data.get('awayTeam', {}).get('abbreviation', ''))

        home_score = game_data.get('home_score', game_data.get('homeScore', ''))
        away_score = game_data.get('away_score', game_data.get('awayScore', ''))

        # Build descriptive text
        text_parts = [f"NBA Game: {away_team} at {home_team}"]

        if date:
            text_parts.append(f"Date: {date}")
        if season:
            text_parts.append(f"Season: {season}")

        if home_score and away_score:
            winner = home_team if int(home_score) > int(away_score) else away_team
            text_parts.append(f"Final Score: {away_team} {away_score}, {home_team} {home_score}")
            text_parts.append(f"Winner: {winner}")

        # Add game type if available
        if 'game_type' in game_data:
            text_parts.append(f"Game Type: {game_data['game_type']}")
        if 'playoffs' in game_data and game_data['playoffs']:
            text_parts.append("Playoff Game")

        return ". ".join(text_parts) + "."

    def generate_play_text(self, play_data: Dict) -> str:
        """
        Generate descriptive text for play-by-play embedding

        Args:
            play_data: Play data from play-by-play

        Returns:
            Formatted text string for embedding
        """
        # Extract play info
        description = play_data.get('text', play_data.get('description', ''))
        quarter = play_data.get('period', play_data.get('quarter', ''))
        time_remaining = play_data.get('clock', play_data.get('time', ''))

        # Build context
        context_parts = []
        if quarter:
            context_parts.append(f"Q{quarter}")
        if time_remaining:
            context_parts.append(f"Time: {time_remaining}")

        context = " - ".join(context_parts) if context_parts else ""

        if context:
            return f"{context}: {description}"
        else:
            return description

    def process_players(self, limit: Optional[int] = None) -> Dict:
        """
        Process player embeddings from raw_data.nba_players

        Args:
            limit: Maximum number of players to process

        Returns:
            Dictionary with processing statistics
        """
        print(f"\n{'='*70}")
        print("Processing Player Embeddings")
        print(f"{'='*70}\n")

        # Create batch ID
        batch_id = f"player_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Log batch start
        self.cursor.execute("""
            INSERT INTO rag.embedding_generation_log
            (batch_id, entity_type, total_records, status, started_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """, (batch_id, 'player', limit or 0, 'running', datetime.now()))
        log_id = self.cursor.fetchone()[0]
        self.conn.commit()

        try:
            # Query players from JSONB storage
            query = """
                SELECT DISTINCT
                    player_id,
                    data
                FROM raw_data.nba_players
                WHERE player_id IS NOT NULL
                ORDER BY player_id
            """

            if limit:
                query += f" LIMIT {limit}"

            self.cursor.execute(query)
            players = self.cursor.fetchall()

            print(f"Found {len(players)} players to process")

            # Process in batches
            batch_stats = self.batch_processor.process_batch(
                data=players,
                text_generator=lambda p: self.generate_player_text(p[1]),
                entity_type='player',
                embedder=self.embedder,
                cursor=self.cursor,
                dry_run=self.dry_run
            )

            # Update statistics
            self.stats['total_processed'] += batch_stats['processed']
            self.stats['total_embedded'] += batch_stats['embedded']
            self.stats['total_failed'] += batch_stats['failed']
            self.stats['total_cost_usd'] += batch_stats['cost_usd']
            self.stats['total_tokens'] += batch_stats['tokens']

            # Update log
            self.cursor.execute("""
                UPDATE rag.embedding_generation_log
                SET processed_records = %s,
                    failed_records = %s,
                    total_tokens = %s,
                    estimated_cost_usd = %s,
                    status = %s,
                    completed_at = %s
                WHERE id = %s;
            """, (
                batch_stats['embedded'],
                batch_stats['failed'],
                batch_stats['tokens'],
                batch_stats['cost_usd'],
                'completed',
                datetime.now(),
                log_id
            ))
            self.conn.commit()

            print(f"\n✅ Player processing complete: {batch_stats['embedded']} embedded, {batch_stats['failed']} failed")

            return batch_stats

        except Exception as e:
            print(f"\n❌ Error processing players: {e}")

            # Update log with error
            self.cursor.execute("""
                UPDATE rag.embedding_generation_log
                SET status = %s,
                    error_message = %s,
                    completed_at = %s
                WHERE id = %s;
            """, ('failed', str(e), datetime.now(), log_id))
            self.conn.commit()

            raise

    def process_games(self, limit: Optional[int] = None) -> Dict:
        """
        Process game embeddings from raw_data.nba_games

        Args:
            limit: Maximum number of games to process

        Returns:
            Dictionary with processing statistics
        """
        print(f"\n{'='*70}")
        print("Processing Game Embeddings")
        print(f"{'='*70}\n")

        # Create batch ID
        batch_id = f"game_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Log batch start
        self.cursor.execute("""
            INSERT INTO rag.embedding_generation_log
            (batch_id, entity_type, total_records, status, started_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """, (batch_id, 'game', limit or 0, 'running', datetime.now()))
        log_id = self.cursor.fetchone()[0]
        self.conn.commit()

        try:
            # Query games from JSONB storage
            query = """
                SELECT DISTINCT
                    game_id,
                    data
                FROM raw_data.nba_games
                WHERE game_id IS NOT NULL
                ORDER BY game_id
            """

            if limit:
                query += f" LIMIT {limit}"

            self.cursor.execute(query)
            games = self.cursor.fetchall()

            print(f"Found {len(games)} games to process")

            # Process in batches
            batch_stats = self.batch_processor.process_batch(
                data=games,
                text_generator=lambda g: self.generate_game_text(g[1]),
                entity_type='game',
                embedder=self.embedder,
                cursor=self.cursor,
                dry_run=self.dry_run
            )

            # Update statistics
            self.stats['total_processed'] += batch_stats['processed']
            self.stats['total_embedded'] += batch_stats['embedded']
            self.stats['total_failed'] += batch_stats['failed']
            self.stats['total_cost_usd'] += batch_stats['cost_usd']
            self.stats['total_tokens'] += batch_stats['tokens']

            # Update log
            self.cursor.execute("""
                UPDATE rag.embedding_generation_log
                SET processed_records = %s,
                    failed_records = %s,
                    total_tokens = %s,
                    estimated_cost_usd = %s,
                    status = %s,
                    completed_at = %s
                WHERE id = %s;
            """, (
                batch_stats['embedded'],
                batch_stats['failed'],
                batch_stats['tokens'],
                batch_stats['cost_usd'],
                'completed',
                datetime.now(),
                log_id
            ))
            self.conn.commit()

            print(f"\n✅ Game processing complete: {batch_stats['embedded']} embedded, {batch_stats['failed']} failed")

            return batch_stats

        except Exception as e:
            print(f"\n❌ Error processing games: {e}")

            # Update log with error
            self.cursor.execute("""
                UPDATE rag.embedding_generation_log
                SET status = %s,
                    error_message = %s,
                    completed_at = %s
                WHERE id = %s;
            """, ('failed', str(e), datetime.now(), log_id))
            self.conn.commit()

            raise

    def print_summary(self):
        """Print pipeline execution summary"""
        print(f"\n{'='*70}")
        print("Embedding Pipeline Summary")
        print(f"{'='*70}\n")

        print(f"Total Processed:  {self.stats['total_processed']:,}")
        print(f"Total Embedded:   {self.stats['total_embedded']:,}")
        print(f"Total Failed:     {self.stats['total_failed']:,}")
        print(f"Total Tokens:     {self.stats['total_tokens']:,}")
        print(f"Total Cost (USD): ${self.stats['total_cost_usd']:.4f}")

        if self.stats['total_embedded'] > 0:
            avg_cost = self.stats['total_cost_usd'] / self.stats['total_embedded']
            print(f"Avg Cost/Embedding: ${avg_cost:.6f}")

        print()

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate vector embeddings for NBA data'
    )
    parser.add_argument(
        '--entity-type',
        choices=['player', 'game', 'all'],
        default='all',
        help='Type of entity to process'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of records to process (for testing)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for processing'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without actually inserting embeddings'
    )

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print("Phase 0.11: RAG Embedding Pipeline")
    print(f"{'='*70}\n")

    if args.dry_run:
        print("⚠️  DRY RUN MODE - No embeddings will be stored\n")

    pipeline = EmbeddingPipeline(
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )

    try:
        if args.entity_type in ['player', 'all']:
            pipeline.process_players(limit=args.limit)

        if args.entity_type in ['game', 'all']:
            pipeline.process_games(limit=args.limit)

        pipeline.print_summary()

        print("\n✅ Pipeline execution complete!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        pipeline.print_summary()
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        pipeline.print_summary()
        sys.exit(1)

    finally:
        pipeline.close()


if __name__ == '__main__':
    main()
