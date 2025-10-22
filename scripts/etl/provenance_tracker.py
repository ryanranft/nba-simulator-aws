#!/usr/bin/env python3
"""
Data Provenance Tracking - Metadata Embedding and Lineage

Provides comprehensive data provenance tracking:
- Embed metadata (scraper version, timestamp, source URL, content hash, validation status)
- S3 object tags for provenance
- Full data lineage for compliance
- Versioning and reproducibility
- Debugging and traceability

Based on Crawl4AI MCP server metadata patterns.

Usage:
    from provenance_tracker import ProvenanceTracker, DataLineage

    # Provenance tracker
    tracker = ProvenanceTracker()
    metadata = await tracker.create_metadata("espn_scraper", "v1.2.3", "https://espn.com/game/123")

    # Data lineage
    lineage = DataLineage()
    await lineage.add_source("espn_scraper", metadata)
    await lineage.add_transformation("data_cleaner", {"method": "normalize"})
    await lineage.add_output("s3://bucket/game_123.json", metadata)

Version: 1.0
Created: October 13, 2025
"""

import asyncio
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import boto3
    from botocore.exceptions import ClientError

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


@dataclass
class ProvenanceMetadata:
    """Provenance metadata structure"""

    # Core identification
    data_id: str
    source_name: str
    source_version: str
    source_url: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Content information
    content_hash: Optional[str] = None
    content_type: str = "application/json"
    content_size: int = 0

    # Validation and quality
    validation_status: str = "pending"
    validation_errors: List[str] = field(default_factory=list)
    quality_score: float = 0.0

    # Processing information
    processing_method: str = "scraping"
    processing_parameters: Dict[str, Any] = field(default_factory=dict)

    # Environment information
    scraper_host: str = "unknown"
    scraper_user: str = "unknown"
    python_version: str = "unknown"

    # Additional metadata
    tags: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "data_id": self.data_id,
            "source_name": self.source_name,
            "source_version": self.source_version,
            "source_url": self.source_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "content_hash": self.content_hash,
            "content_type": self.content_type,
            "content_size": self.content_size,
            "validation_status": self.validation_status,
            "validation_errors": self.validation_errors,
            "quality_score": self.quality_score,
            "processing_method": self.processing_method,
            "processing_parameters": self.processing_parameters,
            "scraper_host": self.scraper_host,
            "scraper_user": self.scraper_user,
            "python_version": self.python_version,
            "tags": self.tags,
            "custom_metadata": self.custom_metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProvenanceMetadata":
        """Create from dictionary"""
        return cls(
            data_id=data["data_id"],
            source_name=data["source_name"],
            source_version=data["source_version"],
            source_url=data.get("source_url"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            content_hash=data.get("content_hash"),
            content_type=data.get("content_type", "application/json"),
            content_size=data.get("content_size", 0),
            validation_status=data.get("validation_status", "pending"),
            validation_errors=data.get("validation_errors", []),
            quality_score=data.get("quality_score", 0.0),
            processing_method=data.get("processing_method", "scraping"),
            processing_parameters=data.get("processing_parameters", {}),
            scraper_host=data.get("scraper_host", "unknown"),
            scraper_user=data.get("scraper_user", "unknown"),
            python_version=data.get("python_version", "unknown"),
            tags=data.get("tags", []),
            custom_metadata=data.get("custom_metadata", {}),
        )


@dataclass
class DataLineageNode:
    """Data lineage node"""

    node_id: str
    node_type: str  # source, transformation, output
    metadata: ProvenanceMetadata
    parent_nodes: List[str] = field(default_factory=list)
    child_nodes: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ProvenanceTracker:
    """Tracks data provenance and metadata"""

    def __init__(self, s3_bucket: str = "nba-sim-raw-data-lake"):
        self.s3_bucket = s3_bucket
        self.logger = logging.getLogger("provenance_tracker")

        # Initialize S3 client
        if HAS_BOTO3:
            self.s3_client = boto3.client("s3")
        else:
            self.s3_client = None
            self.logger.warning("boto3 not available, S3 provenance tracking disabled")

        # Get environment information
        self.host_info = self._get_host_info()

    def _get_host_info(self) -> Dict[str, str]:
        """Get host and environment information"""
        import platform
        import getpass

        return {
            "host": platform.node(),
            "user": getpass.getuser(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        }

    def generate_data_id(self, source_name: str, content: str = "") -> str:
        """Generate unique data ID"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8] if content else ""
        unique_id = str(uuid.uuid4())[:8]

        return f"{source_name}_{timestamp}_{content_hash}_{unique_id}"

    def calculate_content_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def create_metadata(
        self,
        source_name: str,
        source_version: str,
        source_url: Optional[str] = None,
        content: Optional[str] = None,
        content_type: str = "application/json",
        processing_method: str = "scraping",
        processing_parameters: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> ProvenanceMetadata:
        """Create provenance metadata"""
        data_id = self.generate_data_id(source_name, content or "")

        metadata = ProvenanceMetadata(
            data_id=data_id,
            source_name=source_name,
            source_version=source_version,
            source_url=source_url,
            content_hash=self.calculate_content_hash(content) if content else None,
            content_type=content_type,
            content_size=len(content.encode("utf-8")) if content else 0,
            processing_method=processing_method,
            processing_parameters=processing_parameters or {},
            scraper_host=self.host_info["host"],
            scraper_user=self.host_info["user"],
            python_version=self.host_info["python_version"],
            tags=tags or [],
            custom_metadata=custom_metadata or {},
        )

        self.logger.info(f"Created provenance metadata for {data_id}")
        return metadata

    async def update_metadata(
        self, metadata: ProvenanceMetadata, updates: Dict[str, Any]
    ) -> ProvenanceMetadata:
        """Update metadata with new information"""
        metadata.updated_at = datetime.now(timezone.utc)

        # Update fields
        for key, value in updates.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)
            else:
                metadata.custom_metadata[key] = value

        self.logger.info(f"Updated provenance metadata for {metadata.data_id}")
        return metadata

    async def embed_metadata_in_content(
        self, content: str, metadata: ProvenanceMetadata
    ) -> str:
        """Embed metadata in content"""
        if isinstance(content, str):
            try:
                # Try to parse as JSON
                data = json.loads(content)
                data["_provenance"] = metadata.to_dict()
                return json.dumps(data, indent=2)
            except json.JSONDecodeError:
                # Not JSON, add as comment or header
                metadata_json = json.dumps(metadata.to_dict(), indent=2)
                return f"<!-- PROVENANCE_METADATA\n{metadata_json}\n-->\n{content}"
        else:
            # Already parsed data
            content["_provenance"] = metadata.to_dict()
            return content

    async def tag_s3_object(self, s3_key: str, metadata: ProvenanceMetadata) -> bool:
        """Tag S3 object with provenance metadata"""
        if not self.s3_client:
            self.logger.warning("S3 client not available, skipping S3 tagging")
            return False

        try:
            # Convert metadata to S3 tags
            tags = {
                "data-id": metadata.data_id,
                "source-name": metadata.source_name,
                "source-version": metadata.source_version,
                "created-at": metadata.created_at.isoformat(),
                "content-hash": metadata.content_hash or "",
                "validation-status": metadata.validation_status,
                "quality-score": str(metadata.quality_score),
                "processing-method": metadata.processing_method,
            }

            # Add custom metadata as tags (S3 tags have limits)
            for key, value in metadata.custom_metadata.items():
                if len(key) <= 128 and len(str(value)) <= 256:  # S3 tag limits
                    tags[f"custom-{key}"] = str(value)

            # Apply tags
            tag_string = "&".join([f"{k}={v}" for k, v in tags.items()])

            self.s3_client.put_object_tagging(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Tagging={"TagSet": [{"Key": k, "Value": v} for k, v in tags.items()]},
            )

            self.logger.info(f"Tagged S3 object {s3_key} with provenance metadata")
            return True

        except ClientError as e:
            self.logger.error(f"Error tagging S3 object {s3_key}: {e}")
            return False

    async def get_s3_object_tags(self, s3_key: str) -> Optional[Dict[str, str]]:
        """Get S3 object tags"""
        if not self.s3_client:
            return None

        try:
            response = self.s3_client.get_object_tagging(
                Bucket=self.s3_bucket, Key=s3_key
            )

            tags = {}
            for tag in response.get("TagSet", []):
                tags[tag["Key"]] = tag["Value"]

            return tags

        except ClientError as e:
            self.logger.error(f"Error getting S3 object tags for {s3_key}: {e}")
            return None

    async def search_by_provenance(
        self, filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Search for data by provenance criteria"""
        # This would typically query a database or search index
        # For now, we'll return a placeholder
        self.logger.info(f"Searching by provenance filters: {filters}")
        return []


class DataLineage:
    """Manages data lineage and relationships"""

    def __init__(self):
        self.nodes: Dict[str, DataLineageNode] = {}
        self.logger = logging.getLogger("data_lineage")

    async def add_source(
        self, source_id: str, metadata: ProvenanceMetadata
    ) -> DataLineageNode:
        """Add source node to lineage"""
        node = DataLineageNode(node_id=source_id, node_type="source", metadata=metadata)

        self.nodes[source_id] = node
        self.logger.info(f"Added source node: {source_id}")
        return node

    async def add_transformation(
        self,
        transformation_id: str,
        metadata: ProvenanceMetadata,
        parent_nodes: List[str],
    ) -> DataLineageNode:
        """Add transformation node to lineage"""
        node = DataLineageNode(
            node_id=transformation_id,
            node_type="transformation",
            metadata=metadata,
            parent_nodes=parent_nodes,
        )

        # Update parent nodes
        for parent_id in parent_nodes:
            if parent_id in self.nodes:
                self.nodes[parent_id].child_nodes.append(transformation_id)

        self.nodes[transformation_id] = node
        self.logger.info(f"Added transformation node: {transformation_id}")
        return node

    async def add_output(
        self, output_id: str, metadata: ProvenanceMetadata, parent_nodes: List[str]
    ) -> DataLineageNode:
        """Add output node to lineage"""
        node = DataLineageNode(
            node_id=output_id,
            node_type="output",
            metadata=metadata,
            parent_nodes=parent_nodes,
        )

        # Update parent nodes
        for parent_id in parent_nodes:
            if parent_id in self.nodes:
                self.nodes[parent_id].child_nodes.append(output_id)

        self.nodes[output_id] = node
        self.logger.info(f"Added output node: {output_id}")
        return node

    def get_lineage_path(self, node_id: str) -> List[DataLineageNode]:
        """Get lineage path from source to node"""
        if node_id not in self.nodes:
            return []

        path = []
        current_id = node_id

        while current_id in self.nodes:
            node = self.nodes[current_id]
            path.append(node)

            # Move to parent (for sources, there are no parents)
            if node.parent_nodes:
                current_id = node.parent_nodes[0]  # Take first parent
            else:
                break

        return list(reversed(path))  # Return from source to target

    def get_ancestors(self, node_id: str) -> List[DataLineageNode]:
        """Get all ancestor nodes"""
        ancestors = []
        visited = set()

        def _get_ancestors_recursive(current_id: str):
            if current_id in visited or current_id not in self.nodes:
                return

            visited.add(current_id)
            node = self.nodes[current_id]

            for parent_id in node.parent_nodes:
                if parent_id in self.nodes:
                    ancestors.append(self.nodes[parent_id])
                    _get_ancestors_recursive(parent_id)

        _get_ancestors_recursive(node_id)
        return ancestors

    def get_descendants(self, node_id: str) -> List[DataLineageNode]:
        """Get all descendant nodes"""
        descendants = []
        visited = set()

        def _get_descendants_recursive(current_id: str):
            if current_id in visited or current_id not in self.nodes:
                return

            visited.add(current_id)
            node = self.nodes[current_id]

            for child_id in node.child_nodes:
                if child_id in self.nodes:
                    descendants.append(self.nodes[child_id])
                    _get_descendants_recursive(child_id)

        _get_descendants_recursive(node_id)
        return descendants

    def get_lineage_summary(self) -> Dict[str, Any]:
        """Get lineage summary"""
        node_types = {}
        for node in self.nodes.values():
            node_type = node.node_type
            node_types[node_type] = node_types.get(node_type, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "node_types": node_types,
            "sources": [
                n.node_id for n in self.nodes.values() if n.node_type == "source"
            ],
            "transformations": [
                n.node_id
                for n in self.nodes.values()
                if n.node_type == "transformation"
            ],
            "outputs": [
                n.node_id for n in self.nodes.values() if n.node_type == "output"
            ],
        }

    def export_lineage(self) -> Dict[str, Any]:
        """Export lineage as JSON"""
        return {
            "nodes": {
                node_id: {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "metadata": node.metadata.to_dict(),
                    "parent_nodes": node.parent_nodes,
                    "child_nodes": node.child_nodes,
                    "created_at": node.created_at.isoformat(),
                }
                for node_id, node in self.nodes.items()
            },
            "summary": self.get_lineage_summary(),
        }


class ProvenanceManager:
    """Manages provenance tracking across the system"""

    def __init__(self, s3_bucket: str = "nba-sim-raw-data-lake"):
        self.tracker = ProvenanceTracker(s3_bucket)
        self.lineage = DataLineage()
        self.logger = logging.getLogger("provenance_manager")

    async def track_data_creation(
        self,
        source_name: str,
        source_version: str,
        source_url: Optional[str] = None,
        content: Optional[str] = None,
        s3_key: Optional[str] = None,
        **kwargs,
    ) -> ProvenanceMetadata:
        """Track data creation with full provenance"""
        # Create metadata
        metadata = await self.tracker.create_metadata(
            source_name, source_version, source_url, content, **kwargs
        )

        # Add to lineage
        await self.lineage.add_source(metadata.data_id, metadata)

        # Tag S3 object if provided
        if s3_key:
            await self.tracker.tag_s3_object(s3_key, metadata)

        self.logger.info(f"Tracked data creation: {metadata.data_id}")
        return metadata

    async def track_data_transformation(
        self,
        transformation_id: str,
        input_data_ids: List[str],
        transformation_method: str,
        transformation_parameters: Dict[str, Any],
        output_content: Optional[str] = None,
        output_s3_key: Optional[str] = None,
    ) -> ProvenanceMetadata:
        """Track data transformation"""
        # Create metadata for transformation
        metadata = await self.tracker.create_metadata(
            source_name=transformation_id,
            source_version="1.0",
            content=output_content,
            processing_method="transformation",
            processing_parameters={
                "method": transformation_method,
                "parameters": transformation_parameters,
                "input_data_ids": input_data_ids,
            },
        )

        # Add transformation to lineage
        await self.lineage.add_transformation(
            transformation_id, metadata, input_data_ids
        )

        # Tag output if provided
        if output_s3_key:
            await self.tracker.tag_s3_object(output_s3_key, metadata)

        self.logger.info(f"Tracked data transformation: {transformation_id}")
        return metadata

    def get_full_lineage(self, data_id: str) -> Dict[str, Any]:
        """Get full lineage for data"""
        path = self.lineage.get_lineage_path(data_id)
        ancestors = self.lineage.get_ancestors(data_id)
        descendants = self.lineage.get_descendants(data_id)

        return {
            "data_id": data_id,
            "lineage_path": [node.node_id for node in path],
            "ancestors": [node.node_id for node in ancestors],
            "descendants": [node.node_id for node in descendants],
            "full_path": [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "metadata": node.metadata.to_dict(),
                }
                for node in path
            ],
        }


# Example usage
if __name__ == "__main__":

    async def example_usage():
        # Create provenance manager
        manager = ProvenanceManager()

        # Track data creation
        metadata = await manager.track_data_creation(
            source_name="espn_scraper",
            source_version="v1.2.3",
            source_url="https://espn.com/game/123",
            content='{"game_id": "123", "score": "110-108"}',
            s3_key="espn/games/2024/game_123.json",
            tags=["game_data", "espn"],
            custom_metadata={"season": "2024-25", "game_type": "regular"},
        )

        print(f"Created metadata: {metadata.data_id}")

        # Track transformation
        transform_metadata = await manager.track_data_transformation(
            transformation_id="data_cleaner_001",
            input_data_ids=[metadata.data_id],
            transformation_method="normalize_scores",
            transformation_parameters={"method": "standardize"},
            output_content='{"game_id": "123", "normalized_score": 1.2}',
            output_s3_key="processed/games/2024/game_123_normalized.json",
        )

        print(f"Created transformation: {transform_metadata.data_id}")

        # Get lineage
        lineage = manager.get_full_lineage(transform_metadata.data_id)
        print(f"Lineage: {lineage}")

        # Export lineage
        export = manager.lineage.export_lineage()
        print(f"Lineage export: {export['summary']}")

    asyncio.run(example_usage())





