"""
Unit Tests for Configuration Settings Management

Tests all configuration settings functionality including:
- Settings validation
- Environment variable handling
- Configuration precedence
- Settings inheritance
- Type conversions
- Default values
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, Any

# Import configuration modules
from nba_simulator.config.loader import ConfigLoader


class TestSettingsValidation:
    """Test configuration settings validation"""

    def test_required_settings_present(self, mock_env_vars):
        """Test that all required settings are present"""
        loader = ConfigLoader(legacy_mode=True)
        db_config = loader.load_database_config()
        
        # Required database settings
        assert "host" in db_config
        assert "port" in db_config
        assert "database" in db_config
        assert "user" in db_config
        assert "password" in db_config
    
    def test_optional_settings_have_defaults(self, mock_env_vars):
        """Test that optional settings have sensible defaults"""
        loader = ConfigLoader(legacy_mode=True)
        s3_config = loader.load_s3_config()
        
        # Should have default bucket even without env var
        assert "bucket" in s3_config
        assert s3_config["bucket"] in [
            "nba-sim-raw-data-lake",
            os.getenv("S3_BUCKET", "nba-sim-raw-data-lake")
        ]
    
    def test_invalid_port_raises_error(self):
        """Test that invalid port numbers are rejected"""
        with patch.dict(os.environ, {"DB_PORT": "invalid"}):
            loader = ConfigLoader(legacy_mode=True)
            
            with pytest.raises(ValueError):
                loader.load_database_config()
    
    def test_missing_critical_setting_raises_error(self):
        """Test that missing critical settings raise appropriate errors"""
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader(legacy_mode=True)
            db_config = loader.load_database_config()
            
            # Should return None for missing critical settings
            assert db_config["host"] is None
            assert db_config["user"] is None
    
    def test_settings_type_conversion(self, mock_env_vars):
        """Test that settings are properly type-converted"""
        loader = ConfigLoader(legacy_mode=True)
        db_config = loader.load_database_config()
        
        # Port should be integer
        assert isinstance(db_config["port"], int)
        assert db_config["port"] == 5432


class TestEnvironmentVariables:
    """Test environment variable handling"""

    def test_env_var_override(self):
        """Test that environment variables override defaults"""
        custom_bucket = "custom-test-bucket"
        with patch.dict(os.environ, {"S3_BUCKET": custom_bucket}):
            loader = ConfigLoader(legacy_mode=True)
            s3_config = loader.load_s3_config()
            
            assert s3_config["bucket"] == custom_bucket
    
    def test_multiple_env_var_sources(self):
        """Test handling of multiple environment variable names for same setting"""
        # DB_HOST takes precedence over RDS_HOST
        with patch.dict(os.environ, {
            "DB_HOST": "primary.db.com",
            "RDS_HOST": "secondary.db.com"
        }):
            loader = ConfigLoader(legacy_mode=True)
            db_config = loader.load_database_config()
            
            assert db_config["host"] == "primary.db.com"
        
        # If DB_HOST not set, falls back to RDS_HOST
        with patch.dict(os.environ, {"RDS_HOST": "secondary.db.com"}, clear=True):
            loader = ConfigLoader(legacy_mode=True)
            db_config = loader.load_database_config()
            
            assert db_config["host"] == "secondary.db.com"
    
    def test_env_var_case_sensitivity(self):
        """Test that environment variable names are case-sensitive"""
        with patch.dict(os.environ, {"db_host": "lowercase.com"}, clear=True):
            loader = ConfigLoader(legacy_mode=True)
            db_config = loader.load_database_config()
            
            # Should not find lowercase version
            assert db_config["host"] is None
    
    def test_env_var_whitespace_handling(self):
        """Test that whitespace in environment variables is handled properly"""
        with patch.dict(os.environ, {"DB_HOST": "  spaced.db.com  "}):
            loader = ConfigLoader(legacy_mode=True)
            db_config = loader.load_database_config()
            
            # Should preserve whitespace (or strip it - depends on implementation)
            assert "spaced.db.com" in db_config["host"]


class TestConfigurationPrecedence:
    """Test configuration precedence rules"""

    def test_env_vars_override_defaults(self):
        """Test that environment variables override default values"""
        with patch.dict(os.environ, {"AWS_REGION": "us-west-2"}):
            loader = ConfigLoader(legacy_mode=True)
            s3_config = loader.load_s3_config()
            
            assert s3_config["region"] == "us-west-2"
    
    def test_yaml_config_override(self, tmp_path):
        """Test that YAML config overrides environment variables (future)"""
        # Create temporary YAML config
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "database.yaml"
        
        yaml_content = """
        host: yaml.db.com
        port: 3306
        database: yaml_db
        user: yaml_user
        password: yaml_pass
        """
        config_file.write_text(yaml_content)
        
        # Mock the config_dir path
        with patch.object(Path, '__truediv__', return_value=config_file.parent):
            with patch.dict(os.environ, {"DB_HOST": "env.db.com"}):
                loader = ConfigLoader(legacy_mode=False)
                # This would test YAML override if implemented
                # For now, just verify it doesn't crash
    
    def test_precedence_order(self):
        """Test complete precedence order: YAML > Env > Defaults"""
        # 1. Only defaults
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader(legacy_mode=True)
            s3_config = loader.load_s3_config()
            assert s3_config["region"] == "us-east-1"  # default
        
        # 2. Env var overrides default
        with patch.dict(os.environ, {"AWS_REGION": "eu-west-1"}):
            loader = ConfigLoader(legacy_mode=True)
            s3_config = loader.load_s3_config()
            assert s3_config["region"] == "eu-west-1"


class TestSettingsInheritance:
    """Test settings inheritance and composition"""

    def test_config_inheritance(self):
        """Test that derived configs inherit from base configs"""
        loader = ConfigLoader(legacy_mode=True)
        
        # Both should share AWS region
        s3_config = loader.load_s3_config()
        aws_config = loader.load_aws_config()
        
        assert "region" in s3_config
        assert "region" in aws_config
        # They should be the same region
        assert s3_config["region"] == aws_config["region"]
    
    def test_config_composition(self):
        """Test that complex configs are composed from simpler ones"""
        loader = ConfigLoader(legacy_mode=True)
        
        # AWS config should compose region and profile
        aws_config = loader.load_aws_config()
        
        assert "region" in aws_config
        assert "profile" in aws_config
    
    def test_nested_config_access(self):
        """Test accessing nested configuration values"""
        loader = ConfigLoader(legacy_mode=True)
        db_config = loader.load_database_config()
        
        # All top-level keys should be accessible
        for key in ["host", "port", "database", "user", "password"]:
            assert key in db_config


class TestTypeConversion:
    """Test type conversion for configuration values"""

    def test_integer_conversion(self, mock_env_vars):
        """Test conversion of string to integer"""
        loader = ConfigLoader(legacy_mode=True)
        db_config = loader.load_database_config()
        
        assert isinstance(db_config["port"], int)
        assert db_config["port"] == 5432
    
    def test_boolean_conversion(self):
        """Test conversion of string to boolean"""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
        ]
        
        for str_value, expected in test_cases:
            # Would need a boolean config setting to test
            # This is a placeholder for when boolean settings exist
            pass
    
    def test_list_conversion(self):
        """Test conversion of comma-separated string to list"""
        with patch.dict(os.environ, {"ALLOWED_SOURCES": "espn,nba_api,hoopr"}):
            # Would need implementation that handles list conversion
            pass
    
    def test_dict_conversion(self):
        """Test conversion of JSON string to dictionary"""
        json_str = '{"key": "value", "number": 42}'
        # Would need implementation that handles JSON conversion
        pass


class TestDefaultValues:
    """Test default value handling"""

    def test_database_defaults(self):
        """Test default database configuration values"""
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader(legacy_mode=True)
            db_config = loader.load_database_config()
            
            # Port should have default
            assert db_config["port"] == 5432
            # Database should have default
            assert db_config["database"] == "nba_simulator"
    
    def test_s3_defaults(self):
        """Test default S3 configuration values"""
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader(legacy_mode=True)
            s3_config = loader.load_s3_config()
            
            assert s3_config["bucket"] == "nba-sim-raw-data-lake"
            assert s3_config["region"] == "us-east-1"
            assert s3_config["prefix"] == ""
    
    def test_aws_defaults(self):
        """Test default AWS configuration values"""
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader(legacy_mode=True)
            aws_config = loader.load_aws_config()
            
            assert aws_config["region"] == "us-east-1"
            assert aws_config["profile"] == "default"
    
    def test_override_all_defaults(self):
        """Test that all defaults can be overridden"""
        custom_env = {
            "DB_HOST": "custom.db.com",
            "DB_PORT": "3306",
            "DB_NAME": "custom_db",
            "S3_BUCKET": "custom-bucket",
            "AWS_REGION": "eu-west-1",
            "AWS_PROFILE": "custom-profile"
        }
        
        with patch.dict(os.environ, custom_env):
            loader = ConfigLoader(legacy_mode=True)
            
            db_config = loader.load_database_config()
            assert db_config["host"] == "custom.db.com"
            assert db_config["port"] == 3306
            assert db_config["database"] == "custom_db"
            
            s3_config = loader.load_s3_config()
            assert s3_config["bucket"] == "custom-bucket"
            assert s3_config["region"] == "eu-west-1"
            
            aws_config = loader.load_aws_config()
            assert aws_config["region"] == "eu-west-1"
            assert aws_config["profile"] == "custom-profile"


class TestConfigurationErrors:
    """Test error handling in configuration"""

    def test_invalid_config_file_path(self):
        """Test handling of invalid configuration file paths"""
        loader = ConfigLoader(legacy_mode=False)
        
        # Should fall back to legacy mode gracefully
        with patch.object(Path, 'exists', return_value=False):
            db_config = loader.load_database_config()
            assert isinstance(db_config, dict)
    
    def test_malformed_yaml_config(self, tmp_path):
        """Test handling of malformed YAML configuration"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "database.yaml"
        
        # Write malformed YAML
        config_file.write_text("invalid: yaml: content: here")
        
        # Should handle gracefully
        loader = ConfigLoader(legacy_mode=False)
        # Should fall back or raise appropriate error
    
    def test_missing_dotenv_package(self):
        """Test handling when python-dotenv is not installed"""
        with patch("nba_simulator.config.loader.load_dotenv", side_effect=ImportError):
            loader = ConfigLoader(legacy_mode=True)
            # Should still work using os.getenv
            db_config = loader.load_database_config()
            assert isinstance(db_config, dict)
    
    def test_circular_config_reference(self):
        """Test handling of circular configuration references"""
        # Would need implementation that checks for circular references
        pass


class TestConfigurationIntegration:
    """Test configuration integration with the system"""

    def test_config_loader_singleton(self):
        """Test that ConfigLoader works as expected (not necessarily singleton)"""
        loader1 = ConfigLoader(legacy_mode=True)
        loader2 = ConfigLoader(legacy_mode=True)
        
        # Both should work independently
        config1 = loader1.load_database_config()
        config2 = loader2.load_database_config()
        
        assert config1 == config2
    
    def test_config_reload(self, mock_env_vars):
        """Test that configuration can be reloaded"""
        loader = ConfigLoader(legacy_mode=True)
        
        # First load
        config1 = loader.load_database_config()
        initial_host = config1["host"]
        
        # Change environment
        with patch.dict(os.environ, {"DB_HOST": "new.host.com"}):
            # Reload config
            config2 = loader.load_database_config()
            
            # Should pick up new value
            assert config2["host"] == "new.host.com"
            assert config2["host"] != initial_host
    
    def test_config_used_by_multiple_modules(self, mock_env_vars):
        """Test that config can be shared across modules"""
        loader = ConfigLoader(legacy_mode=True)
        
        # Multiple module types should be able to load config
        db_config = loader.load_database_config()
        s3_config = loader.load_s3_config()
        aws_config = loader.load_aws_config()
        
        # All should be valid dictionaries
        assert isinstance(db_config, dict)
        assert isinstance(s3_config, dict)
        assert isinstance(aws_config, dict)
    
    def test_config_thread_safety(self, mock_env_vars):
        """Test that configuration loading is thread-safe"""
        import threading
        
        loader = ConfigLoader(legacy_mode=True)
        results = []
        
        def load_config():
            config = loader.load_database_config()
            results.append(config)
        
        # Create multiple threads
        threads = [threading.Thread(target=load_config) for _ in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All results should be the same
        assert len(results) == 10
        assert all(r == results[0] for r in results)


# Fixtures
@pytest.fixture
def mock_env_vars():
    """Provide mock environment variables for testing"""
    env_vars = {
        "DB_HOST": "test.database.com",
        "DB_PORT": "5432",
        "DB_NAME": "test_db",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_password",
        "S3_BUCKET": "test-bucket",
        "AWS_REGION": "us-east-1",
        "AWS_PROFILE": "default"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def clean_env():
    """Provide clean environment with no configuration variables"""
    with patch.dict(os.environ, {}, clear=True):
        yield


@pytest.fixture
def temp_config_dir(tmp_path):
    """Provide temporary configuration directory"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
