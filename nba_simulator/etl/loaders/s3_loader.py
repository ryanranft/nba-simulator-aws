"""
S3 Loader - AWS S3 Data Lake Storage

Uploads data to S3 data lake (119+ GB, 146,115+ files):
- Raw JSON data
- Extracted datasets
- Processed files
- Backup archives

Features:
- Multipart upload for large files
- Retry with exponential backoff
- Metadata tagging
- Compression support
- Parallel uploads

Based on existing S3 patterns from data lake operations.
"""

from typing import Dict, Any, List, Optional, Tuple, BinaryIO
from pathlib import Path
from datetime import datetime
import json
import gzip
import io
import boto3
from botocore.exceptions import ClientError

from .base_loader import BaseLoader, LoadStatus
from ...config import config


class S3Loader(BaseLoader):
    """
    S3 data lake loader with multipart upload support.
    
    Optimized for uploading large files (>5MB) with retry logic.
    Supports compression and metadata tagging.
    """
    
    def __init__(
        self,
        bucket: Optional[str] = None,
        prefix: str = "",
        compress: bool = False,
        content_type: str = "application/json",
        **kwargs
    ):
        """
        Initialize S3 loader.
        
        Args:
            bucket: S3 bucket name (defaults to config)
            prefix: Key prefix (directory path)
            compress: Gzip compress before upload
            content_type: Content-Type header
            **kwargs: Additional BaseLoader arguments
        """
        super().__init__(**kwargs)
        
        # S3 configuration
        s3_config = config.load_s3_config()
        self.bucket = bucket or s3_config['bucket']
        self.prefix = prefix.rstrip('/') + '/' if prefix else ""
        self.region = s3_config['region']
        self.compress = compress
        self.content_type = content_type
        
        # S3 client
        self.s3_client = None
        self._init_s3_client()
        
        self.logger.info(f"S3 bucket: {self.bucket}")
        self.logger.info(f"Prefix: {self.prefix or '(root)'}")
        self.logger.info(f"Compression: {'enabled' if self.compress else 'disabled'}")
    
    def _init_s3_client(self):
        """Initialize S3 client"""
        aws_config = config.load_aws_config()
        self.s3_client = boto3.client(
            's3',
            region_name=self.region,
            aws_access_key_id=aws_config.get('access_key_id'),
            aws_secret_access_key=aws_config.get('secret_access_key')
        )
    
    async def validate_input(self, data: Any) -> Tuple[bool, str]:
        """
        Validate input data.
        
        Args:
            data: Dict of {filename: content} or list of file paths
            
        Returns:
            (is_valid, error_message)
        """
        if isinstance(data, dict):
            if not data:
                return False, "Empty data dict provided"
            return True, ""
        elif isinstance(data, list):
            if not data:
                return False, "Empty file list provided"
            # Check files exist
            for filepath in data:
                if not Path(filepath).exists():
                    return False, f"File not found: {filepath}"
            return True, ""
        else:
            return False, "Data must be dict or list of file paths"
    
    async def prepare_data(self, data: Any) -> List[Dict[str, Any]]:
        """
        Prepare data for S3 upload.
        
        Args:
            data: Dict of {filename: content} or list of file paths
            
        Returns:
            List of upload items with:
                - key: S3 key
                - content: File content (bytes)
                - metadata: Optional metadata dict
        """
        upload_items = []
        
        if isinstance(data, dict):
            # Dict format: {filename: content}
            for filename, content in data.items():
                item = {
                    'key': self.prefix + filename,
                    'content': self._prepare_content(content),
                    'metadata': {'source': 'dict', 'upload_time': datetime.utcnow().isoformat()}
                }
                upload_items.append(item)
                
        elif isinstance(data, list):
            # List of file paths
            for filepath in data:
                path = Path(filepath)
                with open(path, 'rb') as f:
                    content = f.read()
                
                item = {
                    'key': self.prefix + path.name,
                    'content': self._prepare_content(content),
                    'metadata': {
                        'source': 'file',
                        'original_path': str(filepath),
                        'upload_time': datetime.utcnow().isoformat()
                    }
                }
                upload_items.append(item)
        
        self.logger.info(f"Prepared {len(upload_items)} items for upload")
        return upload_items
    
    def _prepare_content(self, content: Any) -> bytes:
        """
        Prepare content for upload (compress if needed).
        
        Args:
            content: Content to upload (str, dict, bytes)
            
        Returns:
            Bytes ready for upload
        """
        # Convert to bytes
        if isinstance(content, str):
            content_bytes = content.encode('utf-8')
        elif isinstance(content, dict):
            content_bytes = json.dumps(content).encode('utf-8')
        elif isinstance(content, bytes):
            content_bytes = content
        else:
            content_bytes = str(content).encode('utf-8')
        
        # Compress if enabled
        if self.compress:
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='wb') as gz:
                gz.write(content_bytes)
            content_bytes = buffer.getvalue()
        
        return content_bytes
    
    async def load_batch(self, batch: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Upload batch of files to S3.
        
        Args:
            batch: List of upload items
            
        Returns:
            (uploaded, failed)
        """
        uploaded = 0
        failed = 0
        
        for item in batch:
            try:
                success = await self._upload_item(item)
                if success:
                    uploaded += 1
                    self.metrics.bytes_processed += len(item['content'])
                else:
                    failed += 1
                    
            except Exception as e:
                self.logger.error(f"Upload failed for {item['key']}: {e}")
                failed += 1
        
        return uploaded, failed
    
    async def _upload_item(self, item: Dict[str, Any]) -> bool:
        """
        Upload single item to S3.
        
        Args:
            item: Upload item with key, content, metadata
            
        Returns:
            True if successful
        """
        key = item['key']
        content = item['content']
        metadata = item.get('metadata', {})
        
        # Determine if multipart needed (>5MB)
        use_multipart = len(content) > 5 * 1024 * 1024
        
        try:
            if use_multipart:
                return await self._multipart_upload(key, content, metadata)
            else:
                return await self._simple_upload(key, content, metadata)
                
        except ClientError as e:
            self.logger.error(f"S3 upload failed for {key}: {e}")
            return False
    
    async def _simple_upload(
        self,
        key: str,
        content: bytes,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Simple S3 upload for small files.
        
        Args:
            key: S3 key
            content: File content
            metadata: Metadata dict
            
        Returns:
            True if successful
        """
        extra_args = {
            'ContentType': self.content_type,
            'Metadata': {k: str(v) for k, v in metadata.items()}
        }
        
        if self.compress:
            extra_args['ContentEncoding'] = 'gzip'
        
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            **extra_args
        )
        
        self.logger.debug(f"Uploaded: s3://{self.bucket}/{key}")
        return True
    
    async def _multipart_upload(
        self,
        key: str,
        content: bytes,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Multipart upload for large files.
        
        Args:
            key: S3 key
            content: File content
            metadata: Metadata dict
            
        Returns:
            True if successful
        """
        # Initiate multipart upload
        multipart_params = {
            'ContentType': self.content_type,
            'Metadata': {k: str(v) for k, v in metadata.items()}
        }
        
        if self.compress:
            multipart_params['ContentEncoding'] = 'gzip'
        
        response = self.s3_client.create_multipart_upload(
            Bucket=self.bucket,
            Key=key,
            **multipart_params
        )
        
        upload_id = response['UploadId']
        
        # Upload parts (5MB each)
        part_size = 5 * 1024 * 1024
        parts = []
        
        try:
            for i, start in enumerate(range(0, len(content), part_size), 1):
                end = min(start + part_size, len(content))
                part_data = content[start:end]
                
                response = self.s3_client.upload_part(
                    Bucket=self.bucket,
                    Key=key,
                    PartNumber=i,
                    UploadId=upload_id,
                    Body=part_data
                )
                
                parts.append({
                    'ETag': response['ETag'],
                    'PartNumber': i
                })
                
                self.logger.debug(f"Uploaded part {i} for {key}")
            
            # Complete multipart upload
            self.s3_client.complete_multipart_upload(
                Bucket=self.bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            
            self.logger.debug(f"Completed multipart upload: s3://{self.bucket}/{key}")
            return True
            
        except Exception as e:
            # Abort multipart upload on failure
            self.s3_client.abort_multipart_upload(
                Bucket=self.bucket,
                Key=key,
                UploadId=upload_id
            )
            raise
    
    async def verify_load(self, expected_count: int) -> bool:
        """
        Verify uploads by listing S3 objects.
        
        Args:
            expected_count: Expected number of files
            
        Returns:
            True if count matches
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=self.prefix
            )
            
            count = response.get('KeyCount', 0)
            
            if count >= expected_count:
                self.logger.info(f"✓ Verification passed: {count} files in S3")
                return True
            else:
                self.logger.warning(
                    f"⚠️  Count mismatch: Expected {expected_count}, found {count}"
                )
                return False
                
        except Exception as e:
            self.logger.error(f"Verification failed: {e}")
            return False


class ESPNLoader(S3Loader):
    """
    Specialized S3 loader for ESPN data.
    
    Uploads to: s3://nba-sim-raw-data-lake/box_scores/
    - Game JSON files
    - Play-by-play JSON files
    - Schedule data
    """
    
    def __init__(self, **kwargs):
        """Initialize ESPN S3 loader"""
        super().__init__(
            prefix="box_scores/",
            content_type="application/json",
            compress=True,  # ESPN files are large
            **kwargs
        )
        
        self.logger.info("ESPN data loader for S3 data lake")


class BasketballReferenceLoader(S3Loader):
    """
    Specialized S3 loader for Basketball Reference data.
    
    Uploads to: s3://nba-sim-raw-data-lake/basketball_reference/
    - Player stats
    - Team data
    - Game logs
    - Historical data (13-tier system)
    """
    
    def __init__(self, tier: Optional[int] = None, **kwargs):
        """
        Initialize Basketball Reference S3 loader.
        
        Args:
            tier: Tier number (1-13) for hierarchical collection
            **kwargs: Additional S3Loader arguments
        """
        prefix = "basketball_reference/"
        if tier:
            prefix += f"tier_{tier}/"
        
        super().__init__(
            prefix=prefix,
            content_type="application/json",
            compress=True,
            **kwargs
        )
        
        if tier:
            self.logger.info(f"Basketball Reference Tier {tier} loader")
        else:
            self.logger.info("Basketball Reference loader")


__all__ = [
    'S3Loader',
    'ESPNLoader',
    'BasketballReferenceLoader',
]
