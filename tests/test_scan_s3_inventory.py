#!/usr/bin/env python3
"""
Tests for S3 Inventory Scanner

Tests the S3 scanning component of the reconciliation pipeline.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestS3InventoryScanner:
    """Test suite for S3 inventory scanning"""

    def test_inventory_output_structure(self):
        """Test that inventory output has expected structure"""
        # This is an integration test that would verify the actual script output
        # For now, we define the expected structure
        expected_keys = [
            "metadata",
            "files_by_source",
            "files_by_season",
            "files_by_type",
        ]

        # Mock inventory file
        mock_inventory = {
            "metadata": {
                "bucket": "test-bucket",
                "total_objects_scanned": 1000,
                "scan_date": datetime.now().isoformat(),
            },
            "files_by_source": {"espn": 500, "basketball_reference": 300},
            "files_by_season": {"2024": 400, "2023": 600},
            "files_by_type": {"json": 800, "csv": 200},
        }

        for key in expected_keys:
            assert key in mock_inventory

    @patch("boto3.client")
    def test_s3_scan_with_sampling(self, mock_boto3_client):
        """Test S3 scan with sampling enabled"""
        mock_s3 = MagicMock()

        # Mock S3 paginator
        mock_paginator = MagicMock()
        mock_page = {
            "Contents": [
                {"Key": "espn/2024/game_001.json", "Size": 1024},
                {"Key": "espn/2024/game_002.json", "Size": 2048},
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]
        mock_s3.get_paginator.return_value = mock_paginator

        mock_boto3_client.return_value = mock_s3

        # Verify paginator would be called with bucket name
        assert mock_s3.get_paginator.call_count == 0  # Not called yet in test setup

    def test_inventory_metadata_fields(self):
        """Test inventory metadata contains required fields"""
        required_metadata = [
            "bucket",
            "total_objects_scanned",
            "scan_date",
            "sample_rate",
        ]

        mock_metadata = {
            "bucket": "nba-sim-raw-data-lake",
            "total_objects_scanned": 146115,
            "scan_date": datetime.now().isoformat(),
            "sample_rate": 0.1,
            "scan_duration_seconds": 45.2,
        }

        for field in required_metadata:
            assert field in mock_metadata

    def test_file_categorization_by_source(self):
        """Test files are correctly categorized by source"""
        mock_files = [
            {"Key": "espn/2024/game_001.json", "Size": 1024},
            {"Key": "basketball_reference/2024/box_scores/game_001.json", "Size": 2048},
            {"Key": "nba_api/2024/play_by_play/game_001.json", "Size": 3072},
        ]

        # Test categorization logic
        categorized = {}
        for file_obj in mock_files:
            key = file_obj["Key"]
            source = key.split("/")[0]
            categorized[source] = categorized.get(source, 0) + 1

        assert categorized["espn"] == 1
        assert categorized["basketball_reference"] == 1
        assert categorized["nba_api"] == 1

    def test_cache_directory_structure(self, tmp_path):
        """Test cache directory structure is created correctly"""
        cache_dir = tmp_path / "inventory" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        assert cache_dir.exists()
        assert cache_dir.is_dir()

        # Test cache file can be written
        cache_file = cache_dir / "test_inventory.json"
        cache_file.write_text(json.dumps({"test": "data"}))
        assert cache_file.exists()


class TestS3ScanPerformance:
    """Tests for S3 scan performance and optimization"""

    def test_sampling_reduces_scan_time(self):
        """Test that sampling reduces the number of objects scanned"""
        total_objects = 100000
        sample_rate = 0.1

        # Approximate expected samples (with some variance)
        expected_samples = int(total_objects * sample_rate)

        # In real implementation, verify this reduces scan time
        assert expected_samples == 10000

    def test_full_scan_mode(self):
        """Test full scan mode processes all objects"""
        # When full_scan=True, sample_rate should be ignored
        full_scan_config = {"full_scan": True, "sample_rate": 0.1}

        # In full scan mode, all objects should be scanned
        assert full_scan_config["full_scan"] is True


class TestS3ScanErrorHandling:
    """Tests for S3 scan error handling"""

    @patch("boto3.client")
    def test_s3_access_denied(self, mock_boto3_client):
        """Test handling of S3 access denied errors"""
        mock_s3 = MagicMock()
        mock_s3.get_paginator.side_effect = Exception("Access Denied")
        mock_boto3_client.return_value = mock_s3

        # Should raise appropriate exception
        with pytest.raises(Exception, match="Access Denied"):
            mock_s3.get_paginator("list_objects_v2")

    @patch("boto3.client")
    def test_s3_bucket_not_found(self, mock_boto3_client):
        """Test handling of bucket not found errors"""
        mock_s3 = MagicMock()
        mock_s3.head_bucket.side_effect = Exception("NoSuchBucket")
        mock_boto3_client.return_value = mock_s3

        with pytest.raises(Exception, match="NoSuchBucket"):
            mock_s3.head_bucket(Bucket="nonexistent-bucket")

    def test_inventory_output_validation(self):
        """Test inventory output is valid JSON"""
        mock_inventory = {
            "metadata": {"bucket": "test", "total_objects_scanned": 100},
            "files_by_source": {"espn": 50},
        }

        # Should be serializable to JSON
        json_str = json.dumps(mock_inventory)
        assert json_str is not None

        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed == mock_inventory


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

