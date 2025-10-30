#!/usr/bin/env python3
"""
Incremental Updates & Deduplication Manager

Provides comprehensive deduplication and incremental update capabilities:
- Content-based hashing (SHA256) for duplicate detection
- S3 metadata tagging for efficient lookups
- Skip upload if hash exists
- Enhanced checkpoint system with timestamp tracking
- Atomic updates and versioning
- Resume capability for interrupted operations

Based on Crawl4AI MCP server patterns and AWS best practices.

Usage:
    from deduplication_manager import DeduplicationManager, CheckpointManager

    # Deduplication
    dedup_manager = DeduplicationManager()
    is_duplicate = await dedup_manager.check_duplicate(content, "espn/games/2024")

    # Checkpoint management
    checkpoint_manager = CheckpointManager()
    await checkpoint_manager.save_checkpoint("espn_scraper", {"last_date": "2024-10-13"})
    last_state = await checkpoint_manager.load_checkpoint("espn_scraper")

Version: 1.0
Created: October 13, 2025
"""

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
import sys
from dataclasses import dataclass, field

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import boto3
    from botocore.exceptions import ClientError

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    import aiofiles

    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False


@dataclass
class ContentHash:
    """Content hash information"""

    hash_value: str
    content_type: str
    size_bytes: int
    timestamp: datetime
    source_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckpointData:
    """Checkpoint data structure"""

    checkpoint_id: str
    data: Dict[str, Any]
    timestamp: datetime
    version: int = 1
    is_atomic: bool = True


class DeduplicationManager:
    """Manages content deduplication using SHA256 hashing"""

    def __init__(
        self,
        s3_bucket: str = "nba-sim-raw-data-lake",
        local_db_path: str = "data/deduplication.db",
    ):
        self.s3_bucket = s3_bucket
        self.local_db_path = local_db_path
        self.logger = logging.getLogger("deduplication_manager")

        # Initialize S3 client
        if HAS_BOTO3:
            self.s3_client = boto3.client("s3")
        else:
            self.s3_client = None
            self.logger.warning("boto3 not available, S3 deduplication disabled")

        # Initialize local database
        self._init_local_db()

    def _init_local_db(self) -> None:
        """Initialize local SQLite database for hash tracking"""
        if self.local_db_path == ":memory:":
            # For in-memory database, don't create directories
            conn = sqlite3.connect(":memory:")
        else:
            os.makedirs(os.path.dirname(self.local_db_path), exist_ok=True)
            conn = sqlite3.connect(self.local_db_path)

        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS content_hashes (
                    hash_value TEXT PRIMARY KEY,
                    content_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    source_url TEXT,
                    s3_key TEXT,
                    metadata TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_content_type
                ON content_hashes(content_type)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON content_hashes(timestamp)
            """
            )

            conn.commit()

    def calculate_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    async def check_duplicate(
        self, content: str, content_type: str, s3_prefix: str = ""
    ) -> Tuple[bool, Optional[ContentHash]]:
        """Check if content is duplicate"""
        hash_value = self.calculate_hash(content)

        # Check local database first
        local_duplicate = await self._check_local_duplicate(hash_value)
        if local_duplicate:
            return True, local_duplicate

        # Check S3 if available
        if self.s3_client and s3_prefix:
            s3_duplicate = await self._check_s3_duplicate(hash_value, s3_prefix)
            if s3_duplicate:
                return True, s3_duplicate

        return False, None

    async def _check_local_duplicate(self, hash_value: str) -> Optional[ContentHash]:
        """Check for duplicate in local database"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM content_hashes WHERE hash_value = ?", (hash_value,)
                )
                row = cursor.fetchone()

                if row:
                    return ContentHash(
                        hash_value=row[0],
                        content_type=row[1],
                        size_bytes=row[2],
                        timestamp=datetime.fromisoformat(row[3]),
                        source_url=row[4],
                        metadata=json.loads(row[6]) if row[6] else {},
                    )

                return None

        except Exception as e:
            self.logger.error(f"Error checking local duplicate: {e}")
            return None

    async def _check_s3_duplicate(
        self, hash_value: str, s3_prefix: str
    ) -> Optional[ContentHash]:
        """Check for duplicate in S3 using metadata tags"""
        if not self.s3_client:
            return None

        try:
            # Search for objects with matching hash in metadata
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket, Prefix=s3_prefix
            )

            for obj in response.get("Contents", []):
                try:
                    # Get object metadata
                    head_response = self.s3_client.head_object(
                        Bucket=self.s3_bucket, Key=obj["Key"]
                    )

                    metadata = head_response.get("Metadata", {})
                    if metadata.get("content-hash") == hash_value:
                        return ContentHash(
                            hash_value=hash_value,
                            content_type=metadata.get("content-type", "unknown"),
                            size_bytes=obj["Size"],
                            timestamp=obj["LastModified"],
                            source_url=metadata.get("source-url"),
                            metadata=metadata,
                        )

                except ClientError:
                    continue

            return None

        except Exception as e:
            self.logger.error(f"Error checking S3 duplicate: {e}")
            return None

    async def record_content(
        self,
        content: str,
        content_type: str,
        s3_key: Optional[str] = None,
        source_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContentHash:
        """Record content hash in database"""
        hash_value = self.calculate_hash(content)
        content_hash = ContentHash(
            hash_value=hash_value,
            content_type=content_type,
            size_bytes=len(content.encode("utf-8")),
            timestamp=datetime.now(timezone.utc),
            source_url=source_url,
            metadata=metadata or {},
        )

        try:
            with sqlite3.connect(self.local_db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO content_hashes
                    (hash_value, content_type, size_bytes, timestamp, source_url, s3_key, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        hash_value,
                        content_type,
                        content_hash.size_bytes,
                        content_hash.timestamp.isoformat(),
                        source_url,
                        s3_key,
                        json.dumps(metadata or {}),
                    ),
                )
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error recording content hash: {e}")

        return content_hash

    async def get_duplicate_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                # Total hashes
                cursor = conn.execute("SELECT COUNT(*) FROM content_hashes")
                total_hashes = cursor.fetchone()[0]

                # By content type
                cursor = conn.execute(
                    """
                    SELECT content_type, COUNT(*)
                    FROM content_hashes
                    GROUP BY content_type
                """
                )
                by_type = dict(cursor.fetchall())

                # Storage saved (estimated)
                cursor = conn.execute("SELECT SUM(size_bytes) FROM content_hashes")
                total_size = cursor.fetchone()[0] or 0

                return {
                    "total_hashes": total_hashes,
                    "by_content_type": by_type,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                }

        except Exception as e:
            self.logger.error(f"Error getting duplicate stats: {e}")
            return {}


class CheckpointManager:
    """Manages checkpoints for resumable operations"""

    def __init__(self, checkpoint_dir: str = "data/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("checkpoint_manager")
        self._lock = asyncio.Lock()

    async def save_checkpoint(
        self,
        checkpoint_id: str,
        data: Dict[str, Any],
        version: int = 1,
        is_atomic: bool = True,
    ) -> bool:
        """Save checkpoint data"""
        async with self._lock:
            try:
                checkpoint_data = CheckpointData(
                    checkpoint_id=checkpoint_id,
                    data=data,
                    timestamp=datetime.now(timezone.utc),
                    version=version,
                    is_atomic=is_atomic,
                )

                checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
                temp_file = self.checkpoint_dir / f"{checkpoint_id}.tmp"

                # Write to temporary file first (atomic operation)
                checkpoint_json = {
                    "checkpoint_id": checkpoint_data.checkpoint_id,
                    "data": checkpoint_data.data,
                    "timestamp": checkpoint_data.timestamp.isoformat(),
                    "version": checkpoint_data.version,
                    "is_atomic": checkpoint_data.is_atomic,
                }

                if HAS_AIOFILES:
                    async with aiofiles.open(temp_file, "w") as f:
                        await f.write(json.dumps(checkpoint_json, indent=2))
                else:
                    with open(temp_file, "w") as f:
                        json.dump(checkpoint_json, f, indent=2)

                # Atomic move
                temp_file.rename(checkpoint_file)

                self.logger.info(
                    f"Checkpoint saved: {checkpoint_id} (version {version})"
                )
                return True

            except Exception as e:
                self.logger.error(f"Error saving checkpoint {checkpoint_id}: {e}")
                return False

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[CheckpointData]:
        """Load checkpoint data"""
        try:
            checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"

            if not checkpoint_file.exists():
                return None

            if HAS_AIOFILES:
                async with aiofiles.open(checkpoint_file, "r") as f:
                    content = await f.read()
                    checkpoint_json = json.loads(content)
            else:
                with open(checkpoint_file, "r") as f:
                    checkpoint_json = json.load(f)

            return CheckpointData(
                checkpoint_id=checkpoint_json["checkpoint_id"],
                data=checkpoint_json["data"],
                timestamp=datetime.fromisoformat(checkpoint_json["timestamp"]),
                version=checkpoint_json.get("version", 1),
                is_atomic=checkpoint_json.get("is_atomic", True),
            )

        except Exception as e:
            self.logger.error(f"Error loading checkpoint {checkpoint_id}: {e}")
            return None

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete checkpoint"""
        try:
            checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
            if checkpoint_file.exists():
                checkpoint_file.unlink()
                self.logger.info(f"Checkpoint deleted: {checkpoint_id}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"Error deleting checkpoint {checkpoint_id}: {e}")
            return False

    async def list_checkpoints(self) -> List[str]:
        """List all available checkpoints"""
        try:
            checkpoints = []
            for file_path in self.checkpoint_dir.glob("*.json"):
                checkpoints.append(file_path.stem)
            return sorted(checkpoints)

        except Exception as e:
            self.logger.error(f"Error listing checkpoints: {e}")
            return []

    async def cleanup_old_checkpoints(self, max_age_days: int = 30) -> int:
        """Clean up old checkpoints"""
        try:
            cutoff_time = datetime.now(timezone.utc).timestamp() - (
                max_age_days * 24 * 3600
            )
            deleted_count = 0

            for file_path in self.checkpoint_dir.glob("*.json"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1

            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old checkpoints")

            return deleted_count

        except Exception as e:
            self.logger.error(f"Error cleaning up checkpoints: {e}")
            return 0


class IncrementalUpdateManager:
    """Manages incremental updates with deduplication"""

    def __init__(
        self, dedup_manager: DeduplicationManager, checkpoint_manager: CheckpointManager
    ):
        self.dedup_manager = dedup_manager
        self.checkpoint_manager = checkpoint_manager
        self.logger = logging.getLogger("incremental_update_manager")

    async def should_update(
        self, content: str, content_type: str, s3_prefix: str = ""
    ) -> Tuple[bool, Optional[ContentHash]]:
        """Check if content should be updated (not duplicate)"""
        is_duplicate, existing_hash = await self.dedup_manager.check_duplicate(
            content, content_type, s3_prefix
        )

        if is_duplicate:
            self.logger.info(f"Skipping duplicate {content_type} content")
            return False, existing_hash

        return True, None

    async def record_update(
        self,
        content: str,
        content_type: str,
        s3_key: Optional[str] = None,
        source_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContentHash:
        """Record successful update"""
        return await self.dedup_manager.record_content(
            content, content_type, s3_key, source_url, metadata
        )

    async def get_update_stats(self) -> Dict[str, Any]:
        """Get update statistics"""
        dedup_stats = await self.dedup_manager.get_duplicate_stats()
        checkpoints = await self.checkpoint_manager.list_checkpoints()

        return {
            "deduplication": dedup_stats,
            "active_checkpoints": len(checkpoints),
            "checkpoint_list": checkpoints,
        }


# Example usage
if __name__ == "__main__":

    async def example_usage():
        # Create managers
        dedup_manager = DeduplicationManager()
        checkpoint_manager = CheckpointManager()
        update_manager = IncrementalUpdateManager(dedup_manager, checkpoint_manager)

        # Example content
        content = '{"game_id": "12345", "score": "110-108"}'

        # Check if should update
        should_update, existing = await update_manager.should_update(
            content, "game_data", "espn/games/2024"
        )

        print(f"Should update: {should_update}")
        if existing:
            print(f"Existing hash: {existing.hash_value}")

        # Record update if needed
        if should_update:
            content_hash = await update_manager.record_update(
                content, "game_data", "espn/games/2024/game_12345.json"
            )
            print(f"Recorded hash: {content_hash.hash_value}")

        # Save checkpoint
        await checkpoint_manager.save_checkpoint(
            "espn_scraper", {"last_date": "2024-10-13", "processed_games": 150}
        )

        # Load checkpoint
        checkpoint = await checkpoint_manager.load_checkpoint("espn_scraper")
        if checkpoint:
            print(f"Loaded checkpoint: {checkpoint.data}")

        # Get stats
        stats = await update_manager.get_update_stats()
        print(f"Update stats: {stats}")

    asyncio.run(example_usage())
