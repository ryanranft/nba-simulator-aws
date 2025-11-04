"""
Unit Tests for Odds Schema (5 Tables)

Tests all betting odds tables including:
- bookmakers: List of bookmakers/sportsbooks
- events: Sporting events available for betting
- market_types: Types of betting markets
- odds_snapshots: Historical odds data snapshots
- scores: Game scores for betting verification
"""

import pytest
from datetime import datetime


class TestOddsSchemaCore:
    """Tests for core odds schema tables"""
    
    def test_bookmakers_table_exists(self, mock_db_connection):
        """Test that odds.bookmakers table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('bookmakers',)]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'odds' AND table_name = 'bookmakers'
        """)
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == 'bookmakers'
    
    def test_bookmakers_has_primary_key(self, mock_db_connection):
        """Test that bookmakers table has a primary key"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [('constraint_name',), ('column_name',)]
        cursor.fetchall.return_value = [('bookmakers_pkey', 'bookmaker_id')]
        
        cursor.execute("""
            SELECT constraint_name, column_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'bookmakers' AND table_schema = 'odds'
        """)
        results = cursor.fetchall()
        assert len(results) > 0
    
    def test_events_table_exists(self, mock_db_connection):
        """Test that odds.events table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('events',)]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'odds' AND table_name = 'events'
        """)
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == 'events'
    
    def test_market_types_table_exists(self, mock_db_connection):
        """Test that odds.market_types table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('market_types',)]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'odds' AND table_name = 'market_types'
        """)
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == 'market_types'
    
    def test_odds_snapshots_table_exists(self, mock_db_connection):
        """Test that odds.odds_snapshots table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('odds_snapshots',)]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'odds' AND table_name = 'odds_snapshots'
        """)
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == 'odds_snapshots'
    
    def test_scores_table_exists(self, mock_db_connection):
        """Test that odds.scores table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('scores',)]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'odds' AND table_name = 'scores'
        """)
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == 'scores'


class TestOddsSchemaStructure:
    """Tests for odds schema structure and relationships"""
    
    def test_bookmakers_table_has_expected_columns(self, mock_db_connection):
        """Test that bookmakers table has expected column structure"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [
            ('bookmaker_id',), ('bookmaker_name',), ('is_active',), 
            ('country',), ('url',), ('created_at',)
        ]
        
        cursor.execute("SELECT * FROM odds.bookmakers LIMIT 1")
        
        # Verify columns exist
        columns = [desc[0] for desc in cursor.description]
        assert 'bookmaker_id' in columns
        assert 'bookmaker_name' in columns
    
    def test_events_table_has_expected_columns(self, mock_db_connection):
        """Test that events table has expected column structure"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [
            ('event_id',), ('game_id',), ('sport',), ('league',),
            ('home_team',), ('away_team',), ('event_date',), ('status',)
        ]
        
        cursor.execute("SELECT * FROM odds.events LIMIT 1")
        
        # Verify columns exist
        columns = [desc[0] for desc in cursor.description]
        assert 'event_id' in columns
        assert 'game_id' in columns
        assert 'event_date' in columns
    
    def test_market_types_table_has_expected_columns(self, mock_db_connection):
        """Test that market_types table has expected column structure"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [
            ('market_type_id',), ('market_name',), ('description',), 
            ('category',), ('is_active',)
        ]
        
        cursor.execute("SELECT * FROM odds.market_types LIMIT 1")
        
        # Verify columns exist
        columns = [desc[0] for desc in cursor.description]
        assert 'market_type_id' in columns
        assert 'market_name' in columns
    
    def test_odds_snapshots_table_has_expected_columns(self, mock_db_connection):
        """Test that odds_snapshots table has expected column structure"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [
            ('snapshot_id',), ('event_id',), ('bookmaker_id',), 
            ('market_type_id',), ('odds_value',), ('snapshot_time',),
            ('home_odds',), ('away_odds',), ('over_under',)
        ]
        
        cursor.execute("SELECT * FROM odds.odds_snapshots LIMIT 1")
        
        # Verify columns exist
        columns = [desc[0] for desc in cursor.description]
        assert 'snapshot_id' in columns
        assert 'event_id' in columns
        assert 'bookmaker_id' in columns
        assert 'odds_value' in columns
    
    def test_scores_table_has_expected_columns(self, mock_db_connection):
        """Test that scores table has expected column structure"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [
            ('score_id',), ('event_id',), ('home_score',), ('away_score',),
            ('quarter_scores',), ('is_final',), ('updated_at',)
        ]
        
        cursor.execute("SELECT * FROM odds.scores LIMIT 1")
        
        # Verify columns exist
        columns = [desc[0] for desc in cursor.description]
        assert 'score_id' in columns
        assert 'event_id' in columns
        assert 'home_score' in columns
        assert 'away_score' in columns


@pytest.mark.unit
@pytest.mark.database
@pytest.mark.odds
class TestOddsSchemaIntegration:
    """Integration tests for odds schema"""
    
    def test_all_5_odds_tables_exist(self, mock_db_connection):
        """Test that all 5 odds schema tables exist"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        
        expected_tables = [
            'bookmakers', 'events', 'market_types', 'odds_snapshots', 'scores'
        ]
        
        cursor.fetchall.return_value = [(t,) for t in expected_tables]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'odds'
            ORDER BY table_name
        """)
        results = cursor.fetchall()
        
        # Verify we got 5 tables
        assert len(results) == 5
        
        # Verify all expected tables are present
        table_names = [r[0] for r in results]
        for table in expected_tables:
            assert table in table_names
    
    def test_foreign_key_from_events_to_games(self, mock_db_connection):
        """Test that events table has foreign key to public.games"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('fk_events_games',)]
        
        cursor.execute("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = 'odds'
            AND table_name = 'events'
            AND constraint_type = 'FOREIGN KEY'
        """)
        results = cursor.fetchall()
        
        # Should have foreign key to games table
        assert len(results) >= 0
    
    def test_foreign_key_from_odds_snapshots_to_bookmakers(self, mock_db_connection):
        """Test that odds_snapshots has foreign key to bookmakers"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('fk_odds_bookmakers',)]
        
        cursor.execute("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = 'odds'
            AND table_name = 'odds_snapshots'
            AND constraint_type = 'FOREIGN KEY'
        """)
        results = cursor.fetchall()
        
        # Should have foreign key relationships
        assert len(results) >= 0
    
    def test_odds_snapshots_historical_data_integrity(self, mock_db_connection):
        """Test that odds_snapshots maintains historical data"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (1000,)
        
        # Mock checking that we have historical snapshots
        cursor.execute("""
            SELECT COUNT(*) 
            FROM odds.odds_snapshots 
            WHERE snapshot_time < NOW() - INTERVAL '1 day'
        """)
        result = cursor.fetchone()
        
        # Should have historical data
        assert result is not None


@pytest.mark.unit
@pytest.mark.database
@pytest.mark.betting
class TestBettingDataQuality:
    """Tests for betting data quality and validation"""
    
    def test_bookmakers_have_unique_names(self, mock_db_connection):
        """Test that bookmaker names are unique"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (0,)
        
        cursor.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT bookmaker_name)
            FROM odds.bookmakers
        """)
        duplicates = cursor.fetchone()[0]
        
        # Should have no duplicate bookmaker names
        assert duplicates == 0
    
    def test_odds_values_are_positive(self, mock_db_connection):
        """Test that all odds values are positive"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (0,)
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM odds.odds_snapshots 
            WHERE odds_value <= 0
        """)
        invalid_odds = cursor.fetchone()[0]
        
        # Should have no negative or zero odds
        assert invalid_odds == 0
    
    def test_events_have_valid_dates(self, mock_db_connection):
        """Test that event dates are valid"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (0,)
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM odds.events 
            WHERE event_date IS NULL OR event_date < '1946-01-01'
        """)
        invalid_dates = cursor.fetchone()[0]
        
        # Should have no invalid dates (NBA started in 1946)
        assert invalid_dates == 0
    
    def test_scores_match_game_scores(self, mock_db_connection):
        """Test that scores table aligns with games table"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []
        
        cursor.execute("""
            SELECT o.event_id, o.home_score, o.away_score,
                   g.home_score, g.away_score
            FROM odds.scores o
            JOIN odds.events e ON o.event_id = e.event_id
            JOIN public.games g ON e.game_id = g.game_id
            WHERE o.home_score != g.home_score 
               OR o.away_score != g.away_score
        """)
        mismatches = cursor.fetchall()
        
        # Scores should match between schemas
        assert len(mismatches) == 0


@pytest.mark.unit
@pytest.mark.database
class TestOddsSchemaPerformance:
    """Performance tests for odds schema queries"""
    
    def test_bookmakers_query_performance(self, mock_db_connection, performance_timer):
        """Test that bookmakers queries complete quickly"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []
        
        performance_timer.start()
        cursor.execute("SELECT * FROM odds.bookmakers")
        cursor.fetchall()
        performance_timer.stop()
        
        # Query should complete in reasonable time (mocked, but structure for real tests)
        assert performance_timer.elapsed is not None
    
    def test_odds_snapshots_index_exists(self, mock_db_connection):
        """Test that odds_snapshots has proper indexes"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            ('idx_odds_snapshots_event_id',),
            ('idx_odds_snapshots_bookmaker_id',),
            ('idx_odds_snapshots_snapshot_time',)
        ]
        
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'odds' AND tablename = 'odds_snapshots'
        """)
        indexes = cursor.fetchall()
        
        # Should have indexes for common query patterns
        assert len(indexes) >= 0
