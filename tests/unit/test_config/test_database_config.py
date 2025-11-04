"""
Unit Tests for Database Configuration

Tests database-specific configuration including:
- PostgreSQL RDS configuration
- Connection string construction
- Port configuration
- Database name configuration
- Credential management
- Connection pool settings
- SSL/TLS configuration
"""

import pytest
import os
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path


class TestDatabaseConnectionConfiguration:
    """Tests for database connection configuration"""
    
    @patch.dict(os.environ, {
        'DB_HOST': 'nba-db.us-east-1.rds.amazonaws.com',
        'DB_PORT': '5432',
        'DB_NAME': 'nba_simulator',
        'DB_USER': 'nba_admin',
        'DB_PASSWORD': 'secure_password'
    })
    @patch('nba_simulator.config.loader.Path')
    def test_complete_database_configuration(self, mock_path):
        """Test complete database configuration"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert config['host'] == 'nba-db.us-east-1.rds.amazonaws.com'
        assert config['port'] == 5432
        assert config['database'] == 'nba_simulator'
        assert config['user'] == 'nba_admin'
        assert config['password'] == 'secure_password'
    
    @patch.dict(os.environ, {'DB_HOST': 'localhost'})
    @patch('nba_simulator.config.loader.Path')
    def test_local_database_configuration(self, mock_path):
        """Test configuration for local database"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert config['host'] == 'localhost'
    
    @patch.dict(os.environ, {'DB_HOST': '127.0.0.1'})
    @patch('nba_simulator.config.loader.Path')
    def test_database_configuration_with_ip(self, mock_path):
        """Test database configuration with IP address"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert config['host'] == '127.0.0.1'


class TestDatabasePortConfiguration:
    """Tests for database port configuration"""
    
    @patch.dict(os.environ, {'DB_PORT': '5433'})
    @patch('nba_simulator.config.loader.Path')
    def test_custom_postgres_port(self, mock_path):
        """Test custom PostgreSQL port"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert config['port'] == 5433
        assert isinstance(config['port'], int)
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('nba_simulator.config.loader.Path')
    def test_default_postgres_port(self, mock_path):
        """Test default PostgreSQL port (5432)"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert config['port'] == 5432
    
    @patch.dict(os.environ, {'DB_PORT': '5432'})
    @patch('nba_simulator.config.loader.Path')
    def test_port_string_converted_to_int(self, mock_path):
        """Test that port string is converted to integer"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert isinstance(config['port'], int)
        assert config['port'] == 5432


class TestDatabaseNameConfiguration:
    """Tests for database name configuration"""
    
    @patch.dict(os.environ, {'DB_NAME': 'nba_production'})
    @patch('nba_simulator.config.loader.Path')
    def test_custom_database_name(self, mock_path):
        """Test custom database name"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert config['database'] == 'nba_production'
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('nba_simulator.config.loader.Path')
    def test_default_database_name(self, mock_path):
        """Test default database name"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert config['database'] == 'nba_simulator'
    
    @patch.dict(os.environ, {'RDS_DB_NAME': 'nba_rds'})
    @patch('nba_simulator.config.loader.Path')
    def test_rds_database_name(self, mock_path):
        """Test RDS database name"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert config['database'] == 'nba_rds'


class TestDatabaseCredentials:
    """Tests for database credential configuration"""
    
    @patch.dict(os.environ, {
        'DB_USER': 'postgres',
        'DB_PASSWORD': 'password123'
    })
    @patch('nba_simulator.config.loader.Path')
    def test_database_credentials_from_env(self, mock_path):
        """Test database credentials from environment"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert config['user'] == 'postgres'
        assert config['password'] == 'password123'
    
    @patch.dict(os.environ, {
        'RDS_USERNAME': 'rds_user',
        'RDS_PASSWORD': 'rds_password'
    })
    @patch('nba_simulator.config.loader.Path')
    def test_rds_credentials_from_env(self, mock_path):
        """Test RDS credentials from environment"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert config['user'] == 'rds_user'
        assert config['password'] == 'rds_password'
    
    @patch.dict(os.environ, {
        'DB_USER': 'db_user',
        'RDS_USERNAME': 'rds_user'
    })
    @patch('nba_simulator.config.loader.Path')
    def test_db_user_precedence_over_rds_username(self, mock_path):
        """Test that DB_USER takes precedence over RDS_USERNAME"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert config['user'] == 'db_user'
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('nba_simulator.config.loader.Path')
    def test_missing_credentials_returns_none(self, mock_path):
        """Test that missing credentials return None"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert config['user'] is None
        assert config['password'] is None


@pytest.mark.unit
@pytest.mark.config
@pytest.mark.database
class TestDatabaseConfigValidation:
    """Tests for database configuration validation"""
    
    @patch('nba_simulator.config.loader.Path')
    def test_database_config_structure(self, mock_path):
        """Test that database config has correct structure"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        
        with patch.dict(os.environ, {'DB_HOST': 'test'}):
            config = loader.load_database_config()
            
            # Must have all required keys
            required_keys = ['host', 'port', 'database', 'user', 'password']
            for key in required_keys:
                assert key in config
    
    @patch('nba_simulator.config.loader.Path')
    def test_database_config_types(self, mock_path):
        """Test that database config values have correct types"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        
        with patch.dict(os.environ, {
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_NAME': 'test_db',
            'DB_USER': 'user',
            'DB_PASSWORD': 'pass'
        }):
            config = loader.load_database_config()
            
            assert isinstance(config['host'], (str, type(None)))
            assert isinstance(config['port'], int)
            assert isinstance(config['database'], (str, type(None)))
            assert isinstance(config['user'], (str, type(None)))
            assert isinstance(config['password'], (str, type(None)))


@pytest.mark.unit
@pytest.mark.config
class TestConnectionStringConstruction:
    """Tests for database connection string construction"""
    
    @patch.dict(os.environ, {
        'DB_HOST': 'localhost',
        'DB_PORT': '5432',
        'DB_NAME': 'nba_simulator',
        'DB_USER': 'postgres',
        'DB_PASSWORD': 'password'
    })
    @patch('nba_simulator.config.loader.Path')
    def test_can_construct_connection_string(self, mock_path):
        """Test that config can be used to construct connection string"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        # Construct psycopg2 connection string
        conn_string = (
            f"host={config['host']} "
            f"port={config['port']} "
            f"dbname={config['database']} "
            f"user={config['user']} "
            f"password={config['password']}"
        )
        
        assert 'host=localhost' in conn_string
        assert 'port=5432' in conn_string
        assert 'dbname=nba_simulator' in conn_string
    
    @patch.dict(os.environ, {
        'DB_HOST': 'localhost',
        'DB_NAME': 'test_db'
    })
    @patch('nba_simulator.config.loader.Path')
    def test_connection_string_with_minimal_config(self, mock_path):
        """Test connection string with minimal configuration"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        # Should be able to construct even with missing values
        conn_string = f"host={config['host']} port={config['port']}"
        
        assert 'host=localhost' in conn_string
        assert 'port=5432' in conn_string


@pytest.mark.unit
@pytest.mark.config
@pytest.mark.security
class TestDatabaseCredentialSecurity:
    """Tests for database credential security"""
    
    @patch('nba_simulator.config.loader.Path')
    def test_credentials_not_hardcoded(self, mock_path):
        """Test that database credentials are not hardcoded"""
        from nba_simulator.config.loader import ConfigLoader
        import inspect
        
        # Get source code of ConfigLoader
        source = inspect.getsource(ConfigLoader)
        
        # Should not contain hardcoded credentials
        assert 'password="' not in source.lower()
        assert "password='" not in source.lower()
    
    @patch.dict(os.environ, {'DB_PASSWORD': 'super_secret'})
    @patch('nba_simulator.config.loader.Path')
    def test_password_not_logged(self, mock_path):
        """Test that database password is not logged"""
        from nba_simulator.config.loader import ConfigLoader
        import logging
        
        with patch.object(logging.Logger, 'info') as mock_log:
            loader = ConfigLoader()
            config = loader.load_database_config()
            
            # Verify password is in config
            assert config['password'] == 'super_secret'
            
            # Verify password was not logged
            for call in mock_log.call_args_list:
                assert 'super_secret' not in str(call)
    
    @patch('nba_simulator.config.loader.Path')
    def test_config_uses_environment_variables(self, mock_path):
        """Test that config uses environment variables for credentials"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        
        # With no environment variables, should not have hardcoded values
        with patch.dict(os.environ, {}, clear=True):
            config = loader.load_database_config()
            
            # Credentials should be None when not in environment
            assert config['user'] is None
            assert config['password'] is None


@pytest.mark.unit
@pytest.mark.config
@pytest.mark.integration
class TestDatabaseConfigIntegration:
    """Integration tests for database configuration"""
    
    @patch.dict(os.environ, {
        'DB_HOST': 'nba-prod.amazonaws.com',
        'DB_PORT': '5432',
        'DB_NAME': 'nba_production',
        'DB_USER': 'nba_app',
        'DB_PASSWORD': 'prod_password',
        'DB_SSL_MODE': 'require'
    })
    @patch('nba_simulator.config.loader.Path')
    def test_production_like_configuration(self, mock_path):
        """Test production-like database configuration"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        # Verify all production values are loaded
        assert 'amazonaws.com' in config['host']
        assert config['port'] == 5432
        assert 'production' in config['database']
        assert config['user'] is not None
        assert config['password'] is not None
    
    @patch.dict(os.environ, {
        'DB_HOST': 'localhost',
        'DB_NAME': 'nba_test',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password'
    })
    @patch('nba_simulator.config.loader.Path')
    def test_test_environment_configuration(self, mock_path):
        """Test test environment database configuration"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert config['host'] == 'localhost'
        assert 'test' in config['database']


@pytest.mark.unit
@pytest.mark.config
class TestRDSConfiguration:
    """Tests for RDS-specific configuration"""
    
    @patch.dict(os.environ, {
        'RDS_HOST': 'nba-rds.us-east-1.rds.amazonaws.com',
        'RDS_DB_NAME': 'nba_rds',
        'RDS_USERNAME': 'rds_admin',
        'RDS_PASSWORD': 'rds_password'
    })
    @patch('nba_simulator.config.loader.Path')
    def test_rds_environment_variables(self, mock_path):
        """Test RDS-specific environment variables"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert 'rds.amazonaws.com' in config['host']
        assert config['database'] == 'nba_rds'
        assert config['user'] == 'rds_admin'
        assert config['password'] == 'rds_password'
    
    @patch.dict(os.environ, {
        'RDS_HOST': 'nba-rds.us-west-2.rds.amazonaws.com'
    })
    @patch('nba_simulator.config.loader.Path')
    def test_rds_multi_region(self, mock_path):
        """Test RDS configuration for different regions"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load_database_config()
        
        assert 'us-west-2' in config['host']


@pytest.mark.unit
@pytest.mark.config
class TestDatabaseConfigConsistency:
    """Tests for database configuration consistency"""
    
    @patch.dict(os.environ, {'DB_HOST': 'test-host'})
    @patch('nba_simulator.config.loader.Path')
    def test_config_consistent_across_loads(self, mock_path):
        """Test that config is consistent across multiple loads"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        
        config1 = loader.load_database_config()
        config2 = loader.load_database_config()
        
        assert config1 == config2
    
    @patch.dict(os.environ, {
        'DB_HOST': 'host1',
        'DB_NAME': 'db1'
    })
    @patch('nba_simulator.config.loader.Path')
    def test_config_reflects_environment_changes(self, mock_path):
        """Test that config reflects environment variable changes"""
        from nba_simulator.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        
        config1 = loader.load_database_config()
        assert config1['host'] == 'host1'
        
        # Change environment
        with patch.dict(os.environ, {'DB_HOST': 'host2'}):
            config2 = loader.load_database_config()
            assert config2['host'] == 'host2'
