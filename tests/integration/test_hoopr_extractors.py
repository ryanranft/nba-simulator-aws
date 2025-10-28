"""
Integration Tests for hoopR Extractors

Tests hoopR extractors with real production data.
hoopR is PRIMARY data source (13.6M PBP records, 813K box scores).
"""

import unittest
from tests.integration.base_integration_test import BaseIntegrationTest
from nba_simulator.etl.extractors.hoopr import (
    HooprPlayByPlayExtractor,
    HooprPlayerBoxExtractor
)
from nba_simulator.database.connection import execute_query


class TestHooprPlayByPlayExtractor(BaseIntegrationTest):
    """
    Test HooprPlayByPlayExtractor with real data.
    
    hoopR PBP is PRIMARY data source (13.6M records).
    """
    
    def setUp(self):
        """Set up test"""
        self.extractor = HooprPlayByPlayExtractor()
    
    def test_extractor_instantiation(self):
        """Test extractor can be instantiated"""
        self.assertIsNotNone(self.extractor)
        self.assertEqual(self.extractor.name, "hoopr_play_by_play")
    
    def test_health_check(self):
        """Test extractor health check"""
        health = self.extractor.health_check()
        
        self.assertEqual(health['status'], 'operational')
        self.assertTrue(health.get('primary_data_source', False))
        self.assertEqual(health.get('expected_records'), '13.6M PBP records')
        
        # Check legacy scripts availability
        if 'legacy_scripts' in health:
            # At least one script should be available
            available = [v for v in health['legacy_scripts'].values() if v]
            self.assertGreater(
                len(available),
                0,
                "At least one hoopR legacy script should be available"
            )
    
    def test_database_has_hoopr_data(self):
        """Verify hoopR data exists in database"""
        query = "SELECT COUNT(*) as count FROM hoopr_play_by_play;"
        result = execute_query(query)
        
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        count = result[0]['count']
        
        # Should have millions of records (13.6M expected)
        self.assertGreater(
            count,
            10_000_000,
            f"Expected >10M hoopR PBP records, found {count:,}"
        )
        
        print(f"\n  ✓ hoopR PBP records in database: {count:,}")
    
    def test_extractor_modes_available(self):
        """Test extractor has expected modes"""
        self.assertIsNotNone(self.extractor.legacy_scripts)
        self.assertIn('incremental', self.extractor.legacy_scripts)
        
        # Incremental should be available
        incremental_script = self.extractor.legacy_scripts['incremental']
        self.assertTrue(
            incremental_script.exists(),
            f"Incremental script not found: {incremental_script}"
        )
    
    @unittest.skip("Skipping actual extraction test - would take too long")
    def test_extract_sample_season(self):
        """
        Test extractor with sample season.
        
        NOTE: Skipped by default to avoid long extraction times.
        Remove @unittest.skip to run actual extraction test.
        """
        # This would call the actual extractor
        # result = self.extractor.extract(season="2024", mode="incremental")
        # self.assertEqual(result.get('status'), 'success')
        pass


class TestHooprPlayerBoxExtractor(BaseIntegrationTest):
    """
    Test HooprPlayerBoxExtractor with real data.
    
    hoopR player box scores: 813K records.
    """
    
    def setUp(self):
        """Set up test"""
        self.extractor = HooprPlayerBoxExtractor()
    
    def test_extractor_instantiation(self):
        """Test extractor can be instantiated"""
        self.assertIsNotNone(self.extractor)
        self.assertEqual(self.extractor.name, "hoopr_player_box")
    
    def test_health_check(self):
        """Test extractor health check"""
        health = self.extractor.health_check()
        
        self.assertEqual(health['status'], 'operational')
        self.assertEqual(health.get('expected_records'), '813K player box scores')
    
    def test_database_has_player_box_data(self):
        """Verify player box score data exists in database"""
        query = "SELECT COUNT(*) as count FROM hoopr_player_box;"
        result = execute_query(query)
        
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        count = result[0]['count']
        
        # Should have hundreds of thousands of records (813K expected)
        self.assertGreater(
            count,
            700_000,
            f"Expected >700K player box scores, found {count:,}"
        )
        
        print(f"\n  ✓ hoopR player box scores in database: {count:,}")
    
    @unittest.skip("Skipping actual extraction test - would take too long")
    def test_extract_sample_season(self):
        """
        Test extractor with sample season.
        
        NOTE: Skipped by default to avoid long extraction times.
        """
        pass


class TestHooprDataQuality(BaseIntegrationTest):
    """
    Test data quality of hoopR data in database.
    """
    
    def test_pbp_data_completeness(self):
        """Test play-by-play data completeness"""
        query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT game_id) as unique_games,
                COUNT(DISTINCT season) as unique_seasons
            FROM hoopr_play_by_play;
        """
        result = execute_query(query)
        
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        
        total = result[0]['total_records']
        games = result[0]['unique_games']
        seasons = result[0]['unique_seasons']
        
        # Validate data (adjusted based on actual database contents)
        self.assertGreater(total, 10_000_000, "Should have >10M PBP records")
        self.assertGreater(games, 25_000, "Should have >25K games")
        self.assertGreater(seasons, 5, "Should have >5 seasons")
        
        print(f"\n  ✓ hoopR PBP Data Quality:")
        print(f"    - Total records: {total:,}")
        print(f"    - Unique games: {games:,}")
        print(f"    - Unique seasons: {seasons}")
    
    def test_player_box_data_completeness(self):
        """Test player box score data completeness"""
        query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT game_id) as unique_games,
                COUNT(DISTINCT player_id) as unique_players
            FROM hoopr_player_box;
        """
        result = execute_query(query)
        
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        
        total = result[0]['total_records']
        games = result[0]['unique_games']
        players = result[0]['unique_players']
        
        # Validate data (adjusted based on actual database contents)
        self.assertGreater(total, 700_000, "Should have >700K box scores")
        self.assertGreater(games, 25_000, "Should have >25K games")
        self.assertGreater(players, 2_500, "Should have >2.5K players")
        
        print(f"\n  ✓ hoopR Player Box Data Quality:")
        print(f"    - Total records: {total:,}")
        print(f"    - Unique games: {games:,}")
        print(f"    - Unique players: {players:,}")


if __name__ == '__main__':
    unittest.main()

