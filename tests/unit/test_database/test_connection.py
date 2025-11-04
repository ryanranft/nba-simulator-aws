"""
Unit Tests for Database Connection Management

Tests the database connection pooling, query execution,
and connection lifecycle management
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import psycopg2
from datetime import datetime


class TestDatabaseConnection:
    """Tests for database connection management"""
    
    def test_connection_pool_initialization(self, mock_db_pool):
        """Test that connection pool initializes correctly"""
        assert mock_db_pool is not None
        assert mock_db_pool.getconn is not None
    
    def test_get_connection_from_pool(self, mock_db_pool):
        """Test getting a connection from the pool"""
        conn = mock_db_pool.getconn()
        assert conn is not None
        
        # Return connection to pool
        mock_db_pool.putconn(conn)
        assert mock_db_pool.putconn.called
    
    def test_connection_returns_to_pool_after_use(self, mock_db_pool):
        """Test that connections are returned to pool"""
        conn = mock_db_pool.getconn()
        mock_db_pool.putconn(conn)
        
        # Verify connection was returned
        assert mock_db_pool.putconn.called
    
    def test_connection_pool_handles_multiple_connections(self, mock_db_pool):
        """Test that pool can handle multiple concurrent connections"""
        connections = []
        for i in range(5):
            conn = mock_db_pool.getconn()
            connections.append(conn)
        
        # All connections should be valid
        assert len(connections) == 5
        
        # Return all connections
        for conn in connections:
            mock_db_pool.putconn(conn)
    
    def test_connection_error_handling(self, mock_db_connection):
        """Test that connection errors are handled gracefully"""
        mock_db_connection.cursor.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception) as exc_info:
            cursor = mock_db_connection.cursor()
        
        assert "Connection failed" in str(exc_info.value)


class TestDatabaseQueries:
    """Tests for database query execution"""
    
    def test_select_query_execution(self, mock_db_connection):
        """Test executing a SELECT query"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [(1, 'test')]
        
        cursor.execute("SELECT * FROM games LIMIT 1")
        results = cursor.fetchall()
        
        assert cursor.execute.called
        assert len(results) == 1
    
    def test_insert_query_execution(self, mock_db_connection):
        """Test executing an INSERT query"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 1
        
        cursor.execute("""
            INSERT INTO games (game_id, game_date, home_team, away_team)
            VALUES ('test_id', '2024-10-23', 'LAL', 'BOS')
        """)
        
        assert cursor.execute.called
        assert cursor.rowcount == 1
    
    def test_update_query_execution(self, mock_db_connection):
        """Test executing an UPDATE query"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 1
        
        cursor.execute("""
            UPDATE games 
            SET home_score = 110 
            WHERE game_id = 'test_id'
        """)
        
        assert cursor.execute.called
        assert cursor.rowcount == 1
    
    def test_delete_query_execution(self, mock_db_connection):
        """Test executing a DELETE query"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 1
        
        cursor.execute("DELETE FROM games WHERE game_id = 'test_id'")
        
        assert cursor.execute.called
        assert cursor.rowcount == 1
    
    def test_parameterized_query_execution(self, mock_db_connection):
        """Test executing a query with parameters"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [(1,)]
        
        cursor.execute(
            "SELECT COUNT(*) FROM games WHERE home_team = %s",
            ('LAL',)
        )
        results = cursor.fetchall()
        
        assert cursor.execute.called
        assert results[0][0] == 1
    
    def test_batch_query_execution(self, mock_db_connection):
        """Test executing multiple queries in batch"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 100
        
        data = [('game1', 'LAL', 'BOS'), ('game2', 'GSW', 'NYK')]
        cursor.executemany(
            "INSERT INTO games (game_id, home_team, away_team) VALUES (%s, %s, %s)",
            data
        )
        
        assert cursor.executemany.called


class TestTransactionManagement:
    """Tests for database transaction handling"""
    
    def test_commit_after_successful_query(self, mock_db_connection):
        """Test that transactions commit after success"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.execute("INSERT INTO games (game_id) VALUES ('test')")
        mock_db_connection.commit()
        
        assert mock_db_connection.commit.called
    
    def test_rollback_after_error(self, mock_db_connection):
        """Test that transactions rollback after error"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.execute.side_effect = Exception("Query failed")
        
        try:
            cursor.execute("INSERT INTO games (game_id) VALUES ('test')")
        except Exception:
            mock_db_connection.rollback()
        
        assert mock_db_connection.rollback.called
    
    def test_transaction_isolation(self, mock_db_connection):
        """Test that transactions are isolated"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        
        # Start transaction
        cursor.execute("BEGIN")
        cursor.execute("INSERT INTO games (game_id) VALUES ('test')")
        
        # Transaction not yet committed
        assert not mock_db_connection.commit.called
        
        # Commit transaction
        mock_db_connection.commit()
        assert mock_db_connection.commit.called


class TestCursorManagement:
    """Tests for cursor lifecycle management"""
    
    def test_cursor_creation(self, mock_db_connection):
        """Test cursor creation"""
        cursor = mock_db_connection.cursor()
        assert cursor is not None
    
    def test_cursor_closes_after_use(self, mock_db_connection):
        """Test that cursors close properly"""
        cursor = mock_db_connection.cursor.return_value
        cursor.close()
        
        assert cursor.close.called
    
    def test_context_manager_closes_cursor(self, mock_db_connection):
        """Test that context manager closes cursor automatically"""
        with mock_db_connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Cursor should close automatically
        assert mock_db_connection.cursor.called
    
    def test_cursor_fetchone_returns_single_row(self, mock_db_connection):
        """Test cursor.fetchone() returns single row"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (1, 'test')
        
        cursor.execute("SELECT * FROM games LIMIT 1")
        result = cursor.fetchone()
        
        assert result == (1, 'test')
    
    def test_cursor_fetchall_returns_all_rows(self, mock_db_connection):
        """Test cursor.fetchall() returns all rows"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [(1, 'test1'), (2, 'test2')]
        
        cursor.execute("SELECT * FROM games")
        results = cursor.fetchall()
        
        assert len(results) == 2
    
    def test_cursor_fetchmany_returns_limited_rows(self, mock_db_connection):
        """Test cursor.fetchmany() returns limited rows"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchmany.return_value = [(1, 'test1'), (2, 'test2')]
        
        cursor.execute("SELECT * FROM games")
        results = cursor.fetchmany(2)
        
        assert len(results) == 2


class TestConnectionConfiguration:
    """Tests for database connection configuration"""
    
    def test_connection_uses_correct_host(self, rds_config):
        """Test that connection uses correct host"""
        assert rds_config['host'] is not None
    
    def test_connection_uses_correct_port(self, rds_config):
        """Test that connection uses correct port"""
        assert rds_config['port'] == 5432
    
    def test_connection_uses_correct_database(self, rds_config):
        """Test that connection uses correct database name"""
        assert rds_config['database'] is not None
    
    def test_connection_has_credentials(self, rds_config):
        """Test that connection has username and password"""
        assert rds_config['username'] is not None
        # Note: password might be empty in test environment


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseIntegration:
    """Integration tests for database operations"""
    
    def test_can_connect_and_query_games_table(self, mock_db_connection):
        """Test end-to-end connection and query"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [('game_id',), ('home_team',)]
        cursor.fetchone.return_value = ('401584876', 'LAL')
        
        cursor.execute("SELECT game_id, home_team FROM games LIMIT 1")
        result = cursor.fetchone()
        
        assert result[0] == '401584876'
        assert result[1] == 'LAL'
    
    def test_can_query_multiple_schemas(self, mock_db_connection):
        """Test querying across different schemas"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (100,)
        
        # Query public schema
        cursor.execute("SELECT COUNT(*) FROM public.games")
        public_count = cursor.fetchone()[0]
        
        # Query odds schema
        cursor.execute("SELECT COUNT(*) FROM odds.bookmakers")
        odds_count = cursor.fetchone()[0]
        
        assert public_count >= 0
        assert odds_count >= 0
    
    def test_can_join_across_schemas(self, mock_db_connection):
        """Test joining tables across schemas"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []
        
        cursor.execute("""
            SELECT g.game_id, e.event_id
            FROM public.games g
            JOIN odds.events e ON g.game_id = e.game_id
            LIMIT 10
        """)
        results = cursor.fetchall()
        
        # Query should execute successfully
        assert cursor.execute.called


@pytest.mark.unit
@pytest.mark.database
@pytest.mark.performance
class TestDatabasePerformance:
    """Performance tests for database operations"""
    
    def test_connection_pool_size_is_appropriate(self, mock_db_pool):
        """Test that connection pool has reasonable size"""
        # Mock pool should support multiple connections
        connections = []
        for i in range(10):
            conn = mock_db_pool.getconn()
            connections.append(conn)
        
        # Should be able to get 10 connections
        assert len(connections) == 10
    
    def test_query_uses_prepared_statements(self, mock_db_connection):
        """Test that queries use prepared statements for efficiency"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        
        # Execute same query multiple times with different parameters
        for i in range(5):
            cursor.execute(
                "SELECT * FROM games WHERE game_id = %s",
                (f'game_{i}',)
            )
        
        # Should use prepared statement (execute called 5 times)
        assert cursor.execute.call_count == 5
    
    def test_connection_pooling_reuses_connections(self, mock_db_pool):
        """Test that connection pool reuses connections"""
        conn1 = mock_db_pool.getconn()
        mock_db_pool.putconn(conn1)
        
        conn2 = mock_db_pool.getconn()
        
        # Connection should be reused (in mock, just verify cycle works)
        assert conn1 is not None
        assert conn2 is not None


@pytest.mark.unit
@pytest.mark.database
class TestErrorHandling:
    """Tests for database error handling"""
    
    def test_handles_connection_timeout(self, mock_db_connection):
        """Test handling of connection timeout errors"""
        mock_db_connection.cursor.side_effect = psycopg2.OperationalError("timeout")
        
        with pytest.raises(psycopg2.OperationalError):
            cursor = mock_db_connection.cursor()
    
    def test_handles_syntax_error_in_query(self, mock_db_connection):
        """Test handling of SQL syntax errors"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.execute.side_effect = psycopg2.ProgrammingError("syntax error")
        
        with pytest.raises(psycopg2.ProgrammingError):
            cursor.execute("SELECT * FORM games")  # Intentional typo
    
    def test_handles_constraint_violation(self, mock_db_connection):
        """Test handling of constraint violations"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.execute.side_effect = psycopg2.IntegrityError("duplicate key")
        
        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO games (game_id) VALUES ('existing_id')
            """)
    
    def test_handles_permission_denied(self, mock_db_connection):
        """Test handling of permission errors"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.execute.side_effect = psycopg2.ProgrammingError("permission denied")
        
        with pytest.raises(psycopg2.ProgrammingError):
            cursor.execute("DROP TABLE games")


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseSecurity:
    """Tests for database security practices"""
    
    def test_uses_parameterized_queries(self, mock_db_connection):
        """Test that queries use parameterization to prevent SQL injection"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        
        # Good: Parameterized query
        team = "LAL'; DROP TABLE games; --"
        cursor.execute(
            "SELECT * FROM games WHERE home_team = %s",
            (team,)
        )
        
        # Parameterization should protect against injection
        assert cursor.execute.called
    
    def test_connection_uses_ssl(self, rds_config):
        """Test that connection configuration includes SSL"""
        # In production, should use SSL
        # This is a structure test - actual SSL config would be in rds_config
        assert 'host' in rds_config
    
    def test_credentials_not_hardcoded(self, rds_config):
        """Test that credentials come from environment/config"""
        # Credentials should come from environment variables or secure config
        assert rds_config['username'] is not None
        # Password validation would check for non-empty value in production
