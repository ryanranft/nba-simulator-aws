"""
Unit Tests for Configuration Loader

Tests the ConfigLoader class including:
- Initialization in legacy and new modes
- Database configuration loading
- S3 configuration loading
- AWS configuration loading
- Environment variable handling
- YAML file support
- Fallback mechanisms
- Error handling
"""

import pytest
import os
from unittest.mock import Mock, MagicMock, patch, mock_open
from pathlib import Path
import tempfile


class TestConfigLoaderInitialization:
    """Tests for ConfigLoader initialization"""

    @patch("nba_simulator.config.loader.Path")
    def test_config_loader_initializes_in_legacy_mode(self, mock_path):
        """Test that ConfigLoader initializes correctly in legacy mode"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader(legacy_mode=True)

        assert loader.legacy_mode is True
        assert loader.project_root is not None
        assert loader.config_dir is not None

    @patch("nba_simulator.config.loader.Path")
    def test_config_loader_initializes_in_new_mode(self, mock_path):
        """Test that ConfigLoader initializes correctly in new mode"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader(legacy_mode=False)

        assert loader.legacy_mode is False
        assert loader.project_root is not None
        assert loader.config_dir is not None

    @patch("nba_simulator.config.loader.Path")
    def test_config_loader_defaults_to_legacy_mode(self, mock_path):
        """Test that ConfigLoader defaults to legacy mode"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()

        assert loader.legacy_mode is True

    @patch("nba_simulator.config.loader.Path")
    def test_config_loader_sets_project_root(self, mock_path):
        """Test that project_root is set correctly"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()

        assert hasattr(loader, "project_root")
        assert loader.project_root is not None

    @patch("nba_simulator.config.loader.Path")
    def test_config_loader_sets_config_dir(self, mock_path):
        """Test that config_dir is set correctly"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()

        assert hasattr(loader, "config_dir")
        assert loader.config_dir is not None


class TestDatabaseConfigLoading:
    """Tests for database configuration loading"""

    @patch.dict(
        os.environ,
        {
            "DB_HOST": "test-host",
            "DB_PORT": "5432",
            "DB_NAME": "test_db",
            "DB_USER": "test_user",
            "DB_PASSWORD": "test_pass",
        },
    )
    @patch("nba_simulator.config.loader.Path")
    def test_load_database_config_from_environment(self, mock_path):
        """Test loading database config from environment variables"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader(legacy_mode=True)
        config = loader.load_database_config()

        assert config["host"] == "test-host"
        assert config["port"] == 5432
        assert config["database"] == "test_db"
        assert config["user"] == "test_user"
        assert config["password"] == "test_pass"

    @patch.dict(
        os.environ,
        {
            "RDS_HOST": "rds-host",
            "RDS_DB_NAME": "rds_db",
            "RDS_USERNAME": "rds_user",
            "RDS_PASSWORD": "rds_pass",
        },
    )
    @patch("nba_simulator.config.loader.Path")
    def test_load_database_config_from_rds_env_vars(self, mock_path):
        """Test loading database config from RDS environment variables"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader(legacy_mode=True)
        config = loader.load_database_config()

        assert config["host"] == "rds-host"
        assert config["database"] == "rds_db"
        assert config["user"] == "rds_user"
        assert config["password"] == "rds_pass"

    @patch.dict(os.environ, {}, clear=True)
    @patch("nba_simulator.config.loader.Path")
    def test_load_database_config_uses_defaults(self, mock_path):
        """Test that database config uses default values when env vars not set"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader(legacy_mode=True)
        config = loader.load_database_config()

        assert config["port"] == 5432
        assert config["database"] == "nba_simulator"

    @patch("nba_simulator.config.loader.Path")
    def test_load_database_config_in_legacy_mode(self, mock_path):
        """Test that legacy mode calls _load_legacy_db_config"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader(legacy_mode=True)

        with patch.object(
            loader, "_load_legacy_db_config", return_value={"host": "legacy"}
        ):
            config = loader.load_database_config()
            assert config["host"] == "legacy"

    @patch("nba_simulator.config.loader.Path")
    def test_load_database_config_in_new_mode(self, mock_path):
        """Test that new mode calls _load_new_db_config"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader(legacy_mode=False)

        with patch.object(loader, "_load_new_db_config", return_value={"host": "new"}):
            config = loader.load_database_config()
            assert config["host"] == "new"


class TestLegacyDatabaseConfig:
    """Tests for legacy database configuration loading"""

    @patch("nba_simulator.config.loader.Path")
    @patch("nba_simulator.config.loader.load_dotenv")
    def test_loads_dotenv_file_if_exists(self, mock_load_dotenv, mock_path):
        """Test that .env file is loaded if it exists"""
        from nba_simulator.config.loader import ConfigLoader

        # Mock that .env file exists
        mock_env_file = MagicMock()
        mock_env_file.exists.return_value = True
        mock_path.return_value.__truediv__.return_value = mock_env_file

        loader = ConfigLoader(legacy_mode=True)
        with patch.dict(os.environ, {"DB_HOST": "test"}):
            config = loader._load_legacy_db_config()

        assert mock_load_dotenv.called

    @patch("nba_simulator.config.loader.Path")
    def test_handles_missing_dotenv_file(self, mock_path):
        """Test that missing .env file is handled gracefully"""
        from nba_simulator.config.loader import ConfigLoader

        # Mock that .env file doesn't exist
        mock_env_file = MagicMock()
        mock_env_file.exists.return_value = False
        mock_path.return_value.__truediv__.return_value = mock_env_file

        loader = ConfigLoader(legacy_mode=True)

        # Should not raise an error
        with patch.dict(os.environ, {"DB_HOST": "test"}):
            config = loader._load_legacy_db_config()
            assert config is not None

    @patch("nba_simulator.config.loader.Path")
    def test_handles_missing_dotenv_package(self, mock_path):
        """Test that missing python-dotenv package is handled gracefully"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader(legacy_mode=True)

        with patch("nba_simulator.config.loader.load_dotenv", side_effect=ImportError):
            with patch.dict(os.environ, {"DB_HOST": "test"}):
                # Should not raise an error
                config = loader._load_legacy_db_config()
                assert config is not None


class TestNewDatabaseConfig:
    """Tests for new YAML database configuration loading"""

    @patch("nba_simulator.config.loader.Path")
    @patch(
        "builtins.open", new_callable=mock_open, read_data="host: yaml-host\nport: 5432"
    )
    def test_loads_yaml_file_if_exists(self, mock_file, mock_path):
        """Test that YAML config file is loaded if it exists"""
        from nba_simulator.config.loader import ConfigLoader

        # Mock that config file exists
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True

        loader = ConfigLoader(legacy_mode=False)
        loader.config_dir = MagicMock()
        loader.config_dir.__truediv__.return_value = mock_config_file

        with patch("nba_simulator.config.loader.yaml") as mock_yaml:
            mock_yaml.safe_load.return_value = {"host": "yaml-host"}
            config = loader._load_new_db_config()

            assert config["host"] == "yaml-host"

    @patch("nba_simulator.config.loader.Path")
    def test_falls_back_to_legacy_if_yaml_missing(self, mock_path):
        """Test that falls back to legacy if YAML file doesn't exist"""
        from nba_simulator.config.loader import ConfigLoader

        # Mock that config file doesn't exist
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False

        loader = ConfigLoader(legacy_mode=False)
        loader.config_dir = MagicMock()
        loader.config_dir.__truediv__.return_value = mock_config_file

        with patch.object(
            loader, "_load_legacy_db_config", return_value={"host": "legacy"}
        ):
            config = loader._load_new_db_config()
            assert config["host"] == "legacy"

    @patch("nba_simulator.config.loader.Path")
    def test_handles_missing_yaml_package(self, mock_path):
        """Test that missing PyYAML package is handled gracefully"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader(legacy_mode=False)

        with patch("nba_simulator.config.loader.yaml", side_effect=ImportError):
            with patch.object(
                loader, "_load_legacy_db_config", return_value={"host": "legacy"}
            ):
                config = loader._load_new_db_config()
                assert config["host"] == "legacy"


class TestS3ConfigLoading:
    """Tests for S3 configuration loading"""

    @patch.dict(
        os.environ,
        {
            "S3_BUCKET": "test-bucket",
            "AWS_REGION": "us-west-2",
            "S3_PREFIX": "test-prefix",
        },
    )
    @patch("nba_simulator.config.loader.Path")
    def test_load_s3_config_from_environment(self, mock_path):
        """Test loading S3 config from environment variables"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_s3_config()

        assert config["bucket"] == "test-bucket"
        assert config["region"] == "us-west-2"
        assert config["prefix"] == "test-prefix"

    @patch.dict(os.environ, {}, clear=True)
    @patch("nba_simulator.config.loader.Path")
    def test_load_s3_config_uses_defaults(self, mock_path):
        """Test that S3 config uses default values"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_s3_config()

        assert config["bucket"] == "nba-sim-raw-data-lake"
        assert config["region"] == "us-east-1"
        assert config["prefix"] == ""

    @patch.dict(os.environ, {"S3_BUCKET": "custom-bucket"})
    @patch("nba_simulator.config.loader.Path")
    def test_load_s3_config_partial_override(self, mock_path):
        """Test that S3 config can partially override defaults"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_s3_config()

        assert config["bucket"] == "custom-bucket"
        assert config["region"] == "us-east-1"  # Default


class TestAWSConfigLoading:
    """Tests for general AWS configuration loading"""

    @patch.dict(os.environ, {"AWS_REGION": "us-west-1", "AWS_PROFILE": "dev"})
    @patch("nba_simulator.config.loader.Path")
    def test_load_aws_config_from_environment(self, mock_path):
        """Test loading AWS config from environment variables"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_aws_config()

        assert config["region"] == "us-west-1"
        assert config["profile"] == "dev"

    @patch.dict(os.environ, {}, clear=True)
    @patch("nba_simulator.config.loader.Path")
    def test_load_aws_config_uses_defaults(self, mock_path):
        """Test that AWS config uses default values"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_aws_config()

        assert config["region"] == "us-east-1"
        assert config["profile"] == "default"


@pytest.mark.unit
@pytest.mark.config
class TestConfigLoaderIntegration:
    """Integration tests for ConfigLoader"""

    @patch("nba_simulator.config.loader.Path")
    def test_can_load_all_configs(self, mock_path):
        """Test that all config types can be loaded"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()

        with patch.dict(
            os.environ,
            {
                "DB_HOST": "test-host",
                "S3_BUCKET": "test-bucket",
                "AWS_REGION": "us-west-2",
            },
        ):
            db_config = loader.load_database_config()
            s3_config = loader.load_s3_config()
            aws_config = loader.load_aws_config()

            assert db_config is not None
            assert s3_config is not None
            assert aws_config is not None

    @patch("nba_simulator.config.loader.Path")
    def test_configs_are_consistent(self, mock_path):
        """Test that configs loaded multiple times are consistent"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()

        with patch.dict(os.environ, {"DB_HOST": "test-host"}):
            config1 = loader.load_database_config()
            config2 = loader.load_database_config()

            assert config1 == config2


@pytest.mark.unit
@pytest.mark.config
class TestConfigValidation:
    """Tests for configuration validation"""

    @patch("nba_simulator.config.loader.Path")
    def test_database_config_has_required_keys(self, mock_path):
        """Test that database config has all required keys"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()

        with patch.dict(os.environ, {"DB_HOST": "test"}):
            config = loader.load_database_config()

            assert "host" in config
            assert "port" in config
            assert "database" in config
            assert "user" in config
            assert "password" in config

    @patch("nba_simulator.config.loader.Path")
    def test_s3_config_has_required_keys(self, mock_path):
        """Test that S3 config has all required keys"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_s3_config()

        assert "bucket" in config
        assert "region" in config
        assert "prefix" in config

    @patch("nba_simulator.config.loader.Path")
    def test_aws_config_has_required_keys(self, mock_path):
        """Test that AWS config has all required keys"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_aws_config()

        assert "region" in config
        assert "profile" in config

    @patch("nba_simulator.config.loader.Path")
    def test_database_port_is_integer(self, mock_path):
        """Test that database port is converted to integer"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()

        with patch.dict(os.environ, {"DB_PORT": "5432"}):
            config = loader.load_database_config()

            assert isinstance(config["port"], int)
            assert config["port"] == 5432


@pytest.mark.unit
@pytest.mark.config
class TestConfigSingletonPattern:
    """Tests for configuration singleton pattern"""

    def test_config_singleton_is_available(self):
        """Test that config singleton is available for import"""
        from nba_simulator.config import config

        assert config is not None

    def test_config_singleton_is_config_loader(self):
        """Test that config singleton is a ConfigLoader instance"""
        from nba_simulator.config import config
        from nba_simulator.config.loader import ConfigLoader

        assert isinstance(config, ConfigLoader)

    def test_config_singleton_defaults_to_legacy_mode(self):
        """Test that config singleton defaults to legacy mode"""
        from nba_simulator.config import config

        assert config.legacy_mode is True


@pytest.mark.unit
@pytest.mark.config
class TestEnvironmentVariablePrecedence:
    """Tests for environment variable precedence"""

    @patch.dict(os.environ, {"DB_HOST": "db-host", "RDS_HOST": "rds-host"})
    @patch("nba_simulator.config.loader.Path")
    def test_db_host_takes_precedence_over_rds_host(self, mock_path):
        """Test that DB_HOST takes precedence over RDS_HOST"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_database_config()

        assert config["host"] == "db-host"

    @patch.dict(os.environ, {"DB_NAME": "db-name", "RDS_DB_NAME": "rds-db-name"})
    @patch("nba_simulator.config.loader.Path")
    def test_db_name_takes_precedence_over_rds_db_name(self, mock_path):
        """Test that DB_NAME takes precedence over RDS_DB_NAME"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_database_config()

        assert config["database"] == "db-name"


@pytest.mark.unit
@pytest.mark.config
@pytest.mark.security
class TestConfigSecurity:
    """Tests for configuration security practices"""

    @patch("nba_simulator.config.loader.Path")
    def test_passwords_not_logged(self, mock_path):
        """Test that passwords are not logged"""
        from nba_simulator.config.loader import ConfigLoader
        import logging

        with patch.object(logging.Logger, "info") as mock_log:
            loader = ConfigLoader()
            with patch.dict(os.environ, {"DB_PASSWORD": "secret"}):
                config = loader.load_database_config()

                # Verify password is in config
                assert "password" in config

                # Verify password was not logged
                for call in mock_log.call_args_list:
                    assert "secret" not in str(call)

    @patch("nba_simulator.config.loader.Path")
    def test_config_does_not_hardcode_credentials(self, mock_path):
        """Test that credentials are not hardcoded"""
        from nba_simulator.config.loader import ConfigLoader

        loader = ConfigLoader()

        with patch.dict(os.environ, {}, clear=True):
            config = loader.load_database_config()

            # Without env vars, credentials should be None, not hardcoded
            assert config["user"] is None
            assert config["password"] is None
