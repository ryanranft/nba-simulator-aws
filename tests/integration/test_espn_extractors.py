"""
Integration Tests for ESPN Extractors

Tests ESPN extractors with real production data.
ESPN is SECONDARY data source (validation and gap-filling).
"""

import unittest
from tests.integration.base_integration_test import BaseIntegrationTest
from nba_simulator.etl.extractors.espn import (
    ESPNPlayByPlayExtractor,
    ESPNBoxScoresExtractor,
    ESPNScheduleExtractor
)


class TestESPNPlayByPlayExtractor(BaseIntegrationTest):
    """
    Test ESPNPlayByPlayExtractor.
    
    ESPN PBP is for validation and gap-filling.
    """
    
    def setUp(self):
        """Set up test"""
        self.extractor = ESPNPlayByPlayExtractor()
    
    def test_extractor_instantiation(self):
        """Test extractor can be instantiated"""
        self.assertIsNotNone(self.extractor)
        self.assertEqual(self.extractor.name, "espn_play_by_play")
    
    def test_health_check(self):
        """Test extractor health check"""
        health = self.extractor.health_check()
        
        self.assertEqual(health['status'], 'operational')
        self.assertEqual(health.get('data_source'), 'ESPN API')
        self.assertEqual(health.get('purpose'), 'Validation and gap-filling')
        
        # Check legacy scripts availability
        if 'legacy_scripts' in health:
            scripts = health['legacy_scripts']
            # Should have multiple modes
            self.assertGreater(len(scripts), 3, "ESPN should have multiple extraction modes")
            
            # Check which scripts are available
            available = [name for name, exists in scripts.items() if exists]
            print(f"\n  ✓ ESPN PBP modes available: {', '.join(available)}")
    
    def test_extractor_has_multiple_modes(self):
        """Test ESPN extractor has multiple extraction modes"""
        self.assertIsNotNone(self.extractor.legacy_scripts)
        
        # ESPN should have 5 modes: async, incremental, simple, missing, extract
        expected_modes = ['async', 'incremental', 'simple', 'missing', 'extract']
        
        for mode in expected_modes:
            self.assertIn(mode, self.extractor.legacy_scripts)


class TestESPNBoxScoresExtractor(BaseIntegrationTest):
    """Test ESPNBoxScoresExtractor"""
    
    def setUp(self):
        """Set up test"""
        self.extractor = ESPNBoxScoresExtractor()
    
    def test_extractor_instantiation(self):
        """Test extractor can be instantiated"""
        self.assertIsNotNone(self.extractor)
        self.assertEqual(self.extractor.name, "espn_box_scores")
    
    def test_health_check(self):
        """Test extractor health check"""
        health = self.extractor.health_check()
        self.assertEqual(health['status'], 'operational')


class TestESPNScheduleExtractor(BaseIntegrationTest):
    """Test ESPNScheduleExtractor"""
    
    def setUp(self):
        """Set up test"""
        self.extractor = ESPNScheduleExtractor()
    
    def test_extractor_instantiation(self):
        """Test extractor can be instantiated"""
        self.assertIsNotNone(self.extractor)
        self.assertEqual(self.extractor.name, "espn_schedule")
    
    def test_health_check(self):
        """Test extractor health check"""
        health = self.extractor.health_check()
        self.assertEqual(health['status'], 'operational')


if __name__ == '__main__':
    unittest.main()

