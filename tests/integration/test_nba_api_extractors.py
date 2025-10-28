"""
Integration Tests for NBA API Extractors

Tests NBA API extractors.
NBA API provides official statistics and possession data.
"""

import unittest
from tests.integration.base_integration_test import BaseIntegrationTest
from nba_simulator.etl.extractors.nba_api import (
    NBAAPIPlayByPlayExtractor,
    NBAAPIPossessionPanelExtractor
)


class TestNBAAPIPlayByPlayExtractor(BaseIntegrationTest):
    """
    Test NBAAPIPlayByPlayExtractor.
    
    NBA API provides official NBA statistics.
    """
    
    def setUp(self):
        """Set up test"""
        self.extractor = NBAAPIPlayByPlayExtractor()
    
    def test_extractor_instantiation(self):
        """Test extractor can be instantiated"""
        self.assertIsNotNone(self.extractor)
        self.assertEqual(self.extractor.name, "nba_api_play_by_play")
    
    def test_health_check(self):
        """Test extractor health check"""
        health = self.extractor.health_check()
        
        self.assertEqual(health['status'], 'operational')
        self.assertEqual(health.get('data_source'), 'NBA Official API')
        self.assertEqual(health.get('purpose'), 'Official statistics')
        
        # Check legacy scripts
        if 'legacy_scripts' in health:
            scripts = health['legacy_scripts']
            # Should have 2 modes
            self.assertEqual(len(scripts), 2, "NBA API should have 2 modes")
            
            available = [name for name, exists in scripts.items() if exists]
            print(f"\n  ✓ NBA API PBP modes: {', '.join(available)}")
    
    def test_extractor_has_modes(self):
        """Test NBA API extractor has expected modes"""
        self.assertIsNotNone(self.extractor.legacy_scripts)
        
        # NBA API should have async and incremental
        expected_modes = ['async', 'incremental']
        
        for mode in expected_modes:
            self.assertIn(mode, self.extractor.legacy_scripts)
    
    def test_rate_limiting_configured(self):
        """Test NBA API has 1.5s rate limit"""
        self.assertEqual(self.extractor.rate_limit_delay, 1.5)


class TestNBAAPIPossessionPanelExtractor(BaseIntegrationTest):
    """
    Test NBAAPIPossessionPanelExtractor.
    
    Creates possession-level panel data from NBA API.
    """
    
    def setUp(self):
        """Set up test"""
        self.extractor = NBAAPIPossessionPanelExtractor()
    
    def test_extractor_instantiation(self):
        """Test extractor can be instantiated"""
        self.assertIsNotNone(self.extractor)
        self.assertEqual(self.extractor.name, "nba_api_possession_panel")
    
    def test_health_check(self):
        """Test extractor health check"""
        health = self.extractor.health_check()
        
        self.assertEqual(health['status'], 'operational')
        self.assertEqual(health.get('data_type'), 'Possession-level panel data')
        self.assertEqual(health.get('critical_for'), 'Temporal analysis')
    
    def test_fast_rate_limiting(self):
        """Test possession panel has faster rate limit (local processing)"""
        # Works with local data, can be faster
        self.assertEqual(self.extractor.rate_limit_delay, 0.5)


if __name__ == '__main__':
    unittest.main()

