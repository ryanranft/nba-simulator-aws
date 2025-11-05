"""
Unit Tests for AWS Configuration

Tests AWS-specific configuration including:
- S3 bucket configuration
- AWS region settings
- AWS profile management
- Service-specific configurations
- Credential handling
- Multi-region support
"""

import pytest
import os
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path


class TestS3Configuration:
    """Tests for S3-specific configuration"""

    @patch.dict(os.environ, {"S3_BUCKET": "nba-data-prod"})
    @patch("nba_simulator.config.loader.Path")
    def test_s3_bucket_name_configurable(self, mock_path):
        """Test that S3 bucket name is configurable"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_s3_config()

        assert config["bucket"] == "nba-data-prod"

    @patch.dict(os.environ, {"S3_PREFIX": "basketball_reference/"})
    @patch("nba_simulator.config.loader.Path")
    def test_s3_prefix_configurable(self, mock_path):
        """Test that S3 prefix is configurable"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_s3_config()

        assert config["prefix"] == "basketball_reference/"

    @patch.dict(os.environ, {}, clear=True)
    @patch("nba_simulator.config.loader.Path")
    def test_s3_default_bucket_name(self, mock_path):
        """Test default S3 bucket name"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_s3_config()

        assert config["bucket"] == "nba-sim-raw-data-lake"

    @patch.dict(os.environ, {}, clear=True)
    @patch("nba_simulator.config.loader.Path")
    def test_s3_default_prefix_is_empty(self, mock_path):
        """Test that default S3 prefix is empty string"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_s3_config()

        assert config["prefix"] == ""


class TestAWSRegionConfiguration:
    """Tests for AWS region configuration"""

    @patch.dict(os.environ, {"AWS_REGION": "us-west-1"})
    @patch("nba_simulator.config.loader.Path")
    def test_aws_region_configurable(self, mock_path):
        """Test that AWS region is configurable"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()

        # Region should be in both S3 and AWS config
        s3_config = loader.load_s3_config()
        aws_config = loader.load_aws_config()

        assert s3_config["region"] == "us-west-1"
        assert aws_config["region"] == "us-west-1"

    @patch.dict(os.environ, {}, clear=True)
    @patch("nba_simulator.config.loader.Path")
    def test_aws_default_region_is_us_east_1(self, mock_path):
        """Test that default AWS region is us-east-1"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_aws_config()

        assert config["region"] == "us-east-1"

    @patch.dict(os.environ, {"AWS_REGION": "eu-west-1"})
    @patch("nba_simulator.config.loader.Path")
    def test_aws_supports_european_regions(self, mock_path):
        """Test that European AWS regions are supported"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_aws_config()

        assert config["region"] == "eu-west-1"

    @patch.dict(os.environ, {"AWS_REGION": "ap-southeast-1"})
    @patch("nba_simulator.config.loader.Path")
    def test_aws_supports_asia_pacific_regions(self, mock_path):
        """Test that Asia Pacific AWS regions are supported"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_aws_config()

        assert config["region"] == "ap-southeast-1"


class TestAWSProfileConfiguration:
    """Tests for AWS profile configuration"""

    @patch.dict(os.environ, {"AWS_PROFILE": "production"})
    @patch("nba_simulator.config.loader.Path")
    def test_aws_profile_configurable(self, mock_path):
        """Test that AWS profile is configurable"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_aws_config()

        assert config["profile"] == "production"

    @patch.dict(os.environ, {}, clear=True)
    @patch("nba_simulator.config.loader.Path")
    def test_aws_default_profile_is_default(self, mock_path):
        """Test that default AWS profile is 'default'"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_aws_config()

        assert config["profile"] == "default"

    @patch.dict(os.environ, {"AWS_PROFILE": "dev"})
    @patch("nba_simulator.config.loader.Path")
    def test_aws_supports_development_profile(self, mock_path):
        """Test that development AWS profile is supported"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_aws_config()

        assert config["profile"] == "dev"


@pytest.mark.unit
@pytest.mark.config
@pytest.mark.aws
class TestAWSConfigIntegration:
    """Integration tests for AWS configuration"""

    @patch.dict(
        os.environ,
        {
            "AWS_REGION": "us-west-2",
            "AWS_PROFILE": "production",
            "S3_BUCKET": "prod-bucket",
            "S3_PREFIX": "data/",
        },
    )
    @patch("nba_simulator.config.loader.Path")
    def test_aws_config_complete_setup(self, mock_path):
        """Test complete AWS configuration setup"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()

        s3_config = loader.load_s3_config()
        aws_config = loader.load_aws_config()

        # S3 config
        assert s3_config["bucket"] == "prod-bucket"
        assert s3_config["region"] == "us-west-2"
        assert s3_config["prefix"] == "data/"

        # AWS config
        assert aws_config["region"] == "us-west-2"
        assert aws_config["profile"] == "production"

    @patch.dict(os.environ, {"AWS_REGION": "us-east-1", "S3_BUCKET": "bucket1"})
    @patch("nba_simulator.config.loader.Path")
    def test_aws_config_partial_override(self, mock_path):
        """Test that AWS config handles partial overrides"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()

        s3_config = loader.load_s3_config()
        aws_config = loader.load_aws_config()

        # Custom values
        assert s3_config["bucket"] == "bucket1"
        assert s3_config["region"] == "us-east-1"

        # Defaults
        assert s3_config["prefix"] == ""
        assert aws_config["profile"] == "default"


@pytest.mark.unit
@pytest.mark.config
class TestAWSConfigValidation:
    """Tests for AWS configuration validation"""

    @patch("nba_simulator.config.loader.Path")
    def test_s3_bucket_name_is_string(self, mock_path):
        """Test that S3 bucket name is a string"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()

        with patch.dict(os.environ, {"S3_BUCKET": "test-bucket"}):
            config = loader.load_s3_config()
            assert isinstance(config["bucket"], str)

    @patch("nba_simulator.config.loader.Path")
    def test_aws_region_is_string(self, mock_path):
        """Test that AWS region is a string"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()

        with patch.dict(os.environ, {"AWS_REGION": "us-west-2"}):
            config = loader.load_aws_config()
            assert isinstance(config["region"], str)

    @patch("nba_simulator.config.loader.Path")
    def test_s3_prefix_is_string(self, mock_path):
        """Test that S3 prefix is a string"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()

        with patch.dict(os.environ, {"S3_PREFIX": "test/"}):
            config = loader.load_s3_config()
            assert isinstance(config["prefix"], str)


@pytest.mark.unit
@pytest.mark.config
@pytest.mark.security
class TestAWSCredentialSecurity:
    """Tests for AWS credential security"""

    @patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
            "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        },
    )
    @patch("nba_simulator.config.loader.Path")
    def test_aws_credentials_not_in_config_objects(self, mock_path):
        """Test that AWS credentials are not returned in config objects"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()

        s3_config = loader.load_s3_config()
        aws_config = loader.load_aws_config()

        # Credentials should not be in config objects
        # (They should be handled by boto3 automatically)
        assert "access_key_id" not in s3_config
        assert "secret_access_key" not in s3_config
        assert "access_key_id" not in aws_config
        assert "secret_access_key" not in aws_config

    @patch("nba_simulator.config.loader.Path")
    def test_config_does_not_log_credentials(self, mock_path):
        """Test that credentials are not logged"""
        from nba_simulator.config.loader import ConfigLoader
        import logging

        with patch.object(logging.Logger, "info") as mock_log:
            loader = ConfigLoader()

            with patch.dict(os.environ, {"AWS_SECRET_ACCESS_KEY": "secret-key"}):
                config = loader.load_aws_config()

                # Verify credentials were not logged
                for call in mock_log.call_args_list:
                    assert "secret-key" not in str(call)


@pytest.mark.unit
@pytest.mark.config
class TestS3PathConstruction:
    """Tests for S3 path construction"""

    @patch.dict(os.environ, {"S3_BUCKET": "test-bucket", "S3_PREFIX": "data/"})
    @patch("nba_simulator.config.loader.Path")
    def test_s3_path_with_prefix(self, mock_path):
        """Test constructing S3 path with prefix"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_s3_config()

        # Construct full S3 path
        s3_path = f"s3://{config['bucket']}/{config['prefix']}file.json"

        assert s3_path == "s3://test-bucket/data/file.json"

    @patch.dict(os.environ, {"S3_BUCKET": "test-bucket"})
    @patch("nba_simulator.config.loader.Path")
    def test_s3_path_without_prefix(self, mock_path):
        """Test constructing S3 path without prefix"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_s3_config()

        # Construct full S3 path
        s3_path = f"s3://{config['bucket']}/{config['prefix']}file.json"

        assert s3_path == "s3://test-bucket/file.json"


@pytest.mark.unit
@pytest.mark.config
class TestMultiRegionSupport:
    """Tests for multi-region AWS deployments"""

    @patch.dict(
        os.environ, {"AWS_REGION": "us-west-2", "AWS_REGION_SECONDARY": "us-east-1"}
    )
    @patch("nba_simulator.config.loader.Path")
    def test_primary_region_from_env(self, mock_path):
        """Test that primary region is loaded from environment"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_aws_config()

        assert config["region"] == "us-west-2"

    @patch.dict(os.environ, {"AWS_REGION": "eu-central-1"})
    @patch("nba_simulator.config.loader.Path")
    def test_supports_all_aws_regions(self, mock_path):
        """Test that all AWS regions are supported"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_aws_config()

        # Any region string should be accepted
        assert isinstance(config["region"], str)
        assert len(config["region"]) > 0
