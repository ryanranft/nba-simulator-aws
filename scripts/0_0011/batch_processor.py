#!/usr/bin/env python3
"""
Phase 0.0011: Batch Processor for Embeddings

Purpose: Process embeddings in batches with progress tracking
Created: October 25, 2025
Implementation ID: rec_034_pgvector

Usage:
    processor = BatchProcessor(batch_size=100)
    stats = processor.process_batch(data, text_generator, embedder, cursor)
"""

import time
from typing import List, Dict, Callable, Optional, Any
from datetime import datetime
from psycopg2.extras import Json


class BatchProcessor:
    """
    Process embeddings in batches with progress tracking and error handling
    """

    def __init__(self, batch_size: int = 100):
        """
        Initialize batch processor

        Args:
            batch_size: Number of records to process per batch
        """
        self.batch_size = batch_size

    def process_batch(
        self,
        data: List[Any],
        text_generator: Callable,
        entity_type: str,
        embedder: Any,
        cursor: Any,
        dry_run: bool = False,
    ) -> Dict:
        """
        Process a batch of data and generate embeddings

        Args:
            data: List of data records (tuples of (entity_id, data))
            text_generator: Function to generate text from data
            entity_type: Type of entity ('player', 'game', etc.)
            embedder: OpenAIEmbedder instance
            cursor: Database cursor
            dry_run: If True, don't actually insert embeddings

        Returns:
            Dictionary with processing statistics
        """
        total = len(data)
        processed = 0
        embedded = 0
        failed = 0
        total_tokens = 0
        total_cost = 0.0

        start_time = time.time()

        print(
            f"\nProcessing {total} {entity_type}(s) in batches of {self.batch_size}..."
        )

        # Process in batches
        for batch_start in range(0, total, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total)
            batch = data[batch_start:batch_end]

            batch_num = (batch_start // self.batch_size) + 1
            total_batches = (total + self.batch_size - 1) // self.batch_size

            print(f"\n--- Batch {batch_num}/{total_batches} ({len(batch)} records) ---")

            # Process each record in batch
            for i, record in enumerate(batch):
                entity_id = record[0]
                entity_data = record[1]

                try:
                    # Generate text description
                    text_content = text_generator(record)

                    if not text_content:
                        print(f"  ⚠️  Skipping {entity_id}: Empty text content")
                        failed += 1
                        continue

                    # Check if already embedded
                    cursor.execute(
                        """
                        SELECT id FROM rag.nba_embeddings
                        WHERE entity_type = %s AND entity_id = %s;
                    """,
                        (entity_type, entity_id),
                    )

                    if cursor.fetchone():
                        # Already exists, skip
                        processed += 1
                        if processed % 10 == 0:
                            print(f"  ✓ Skipped {processed}/{total} (already exists)")
                        continue

                    # Generate embedding
                    embedding = embedder.generate_embedding(text_content)

                    if embedding is None:
                        print(f"  ❌ Failed to generate embedding for {entity_id}")
                        failed += 1
                        continue

                    # Store embedding in database
                    if not dry_run:
                        # Extract metadata from entity_data
                        metadata = self._extract_metadata(entity_data, entity_type)

                        cursor.execute(
                            """
                            INSERT INTO rag.nba_embeddings
                            (entity_type, entity_id, text_content, embedding, metadata)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (entity_type, entity_id)
                            DO UPDATE SET
                                text_content = EXCLUDED.text_content,
                                embedding = EXCLUDED.embedding,
                                metadata = EXCLUDED.metadata,
                                updated_at = NOW();
                        """,
                            (
                                entity_type,
                                entity_id,
                                text_content,
                                embedding,
                                Json(metadata),
                            ),
                        )

                    processed += 1
                    embedded += 1

                    # Progress update
                    if processed % 10 == 0 or processed == total:
                        elapsed = time.time() - start_time
                        rate = processed / elapsed if elapsed > 0 else 0
                        eta = (total - processed) / rate if rate > 0 else 0

                        print(
                            f"  ✓ Processed {processed}/{total} ({processed/total*100:.1f}%) - "
                            f"{rate:.1f} records/sec - ETA: {eta/60:.1f} min"
                        )

                except Exception as e:
                    print(f"  ❌ Error processing {entity_id}: {e}")
                    failed += 1
                    continue

            # Commit after each batch
            if not dry_run:
                cursor.connection.commit()
                print(f"  ✓ Batch {batch_num} committed to database")

            # Brief pause between batches to avoid rate limits
            if batch_end < total:
                time.sleep(0.5)

        # Calculate final statistics
        elapsed = time.time() - start_time

        # Get embedder stats
        embedder_stats = embedder.get_stats()
        total_tokens = embedder_stats.get("total_tokens", 0)
        total_cost = embedder_stats.get("total_cost_usd", 0.0)

        stats = {
            "processed": processed,
            "embedded": embedded,
            "failed": failed,
            "tokens": total_tokens,
            "cost_usd": total_cost,
            "elapsed_seconds": elapsed,
            "rate": processed / elapsed if elapsed > 0 else 0,
        }

        # Print batch summary
        print(f"\n{'='*60}")
        print(f"Batch Processing Complete")
        print(f"{'='*60}")
        print(f"Processed:       {processed:,}/{total:,}")
        print(f"Embedded:        {embedded:,}")
        print(f"Failed:          {failed:,}")
        print(f"Elapsed Time:    {elapsed/60:.2f} minutes")
        print(f"Processing Rate: {stats['rate']:.1f} records/sec")
        print(f"Total Tokens:    {total_tokens:,}")
        print(f"Total Cost:      ${total_cost:.4f}")
        print(f"{'='*60}\n")

        return stats

    def _extract_metadata(self, entity_data: Dict, entity_type: str) -> Dict:
        """
        Extract relevant metadata from entity data

        Args:
            entity_data: Entity data dictionary
            entity_type: Type of entity

        Returns:
            Metadata dictionary
        """
        metadata = {}

        if entity_type == "player":
            # Extract player metadata
            if "team" in entity_data:
                metadata["team"] = entity_data["team"]
            if "team_abbr" in entity_data:
                metadata["team"] = entity_data["team_abbr"]
            if "position" in entity_data:
                metadata["position"] = entity_data["position"]
            if "pos" in entity_data:
                metadata["position"] = entity_data["pos"]
            if "player_name" in entity_data:
                metadata["player_name"] = entity_data["player_name"]
            if "displayName" in entity_data:
                metadata["player_name"] = entity_data["displayName"]

            # Add season info
            if "season" in entity_data:
                metadata["season"] = entity_data["season"]

        elif entity_type == "game":
            # Extract game metadata
            if "season" in entity_data:
                metadata["season"] = entity_data["season"]
            if "game_date" in entity_data:
                metadata["game_date"] = entity_data["game_date"]
            if "date" in entity_data:
                metadata["game_date"] = entity_data["date"]
            if "home_team" in entity_data:
                metadata["home_team"] = entity_data["home_team"]
            if "homeTeam" in entity_data and "abbreviation" in entity_data["homeTeam"]:
                metadata["home_team"] = entity_data["homeTeam"]["abbreviation"]
            if "away_team" in entity_data:
                metadata["away_team"] = entity_data["away_team"]
            if "awayTeam" in entity_data and "abbreviation" in entity_data["awayTeam"]:
                metadata["away_team"] = entity_data["awayTeam"]["abbreviation"]

            # Add game type
            if "game_type" in entity_data:
                metadata["game_type"] = entity_data["game_type"]
            if "playoffs" in entity_data:
                metadata["playoffs"] = entity_data["playoffs"]

        return metadata


# Example usage
if __name__ == "__main__":
    print("Batch Processor - Example Usage")
    print("=" * 50)
    print()
    print("The BatchProcessor is designed to be used by")
    print("the embedding_pipeline.py script.")
    print()
    print("Usage:")
    print("  processor = BatchProcessor(batch_size=100)")
    print("  stats = processor.process_batch(")
    print("      data=records,")
    print("      text_generator=text_func,")
    print("      entity_type='player',")
    print("      embedder=embedder_instance,")
    print("      cursor=db_cursor")
    print("  )")
    print()
